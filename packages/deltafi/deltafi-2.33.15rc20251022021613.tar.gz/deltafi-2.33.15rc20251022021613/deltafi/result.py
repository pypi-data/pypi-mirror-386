#
#    DeltaFi - Data transformation and enrichment platform
#
#    Copyright 2021-2025 DeltaFi Contributors <deltafi@deltafi.org>
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#

import abc
import uuid
from enum import Enum

from deltafi.domain import Content, Context
from deltafi.metric import Metric
from deltafi.resultmessage import LogMessage


class Result:
    __metaclass__ = abc.ABCMeta

    def __init__(self, result_key, result_type, context):
        self.result_key = result_key
        self.result_type = result_type
        self.messages = []
        self.metrics = []
        self.context = context

    @abc.abstractmethod
    def response(self):
        pass

    def add_metric(self, metric: Metric):
        self.metrics.append(metric)
        return self

    def log_info(self, message: str):
        self.messages.append(LogMessage.info(self.context.action_name, message))
        return self

    def log_warning(self, message: str):
        self.messages.append(LogMessage.warning(self.context.action_name, message))
        return self

    def log_error(self, message: str):
        self.messages.append(LogMessage.error(self.context.action_name, message))
        return self


class EgressResult(Result):
    def __init__(self, context: Context):
        super().__init__(None, 'EGRESS', context)

    def response(self):
        return None


class ErrorResult(Result):
    def __init__(self, context: Context, error_cause: str, error_context: str):
        super().__init__('error', 'ERROR', context)
        self.error_cause = error_cause
        self.error_context = error_context
        self.annotations = {}

    def annotate(self, key: str, value: str):
        self.annotations[key] = value
        return self

    def response(self):
        self.log_error(self.error_cause + '\n' + self.error_context)
        return {
            'cause': self.error_cause,
            'context': self.error_context,
            'annotations': self.annotations
        }


class FilterResult(Result):
    def __init__(self, context: Context, filtered_cause: str, filtered_context: str = None):
        super().__init__('filter', 'FILTER', context)
        self.filtered_cause = filtered_cause
        self.filtered_context = filtered_context
        self.annotations = {}

    def annotate(self, key: str, value: str):
        self.annotations[key] = value
        return self

    def response(self):
        return {
            'message': self.filtered_cause,
            'context': self.filtered_context,
            'annotations': self.annotations
        }


class IngressResultItem:
    def __init__(self, context: Context, delta_file_name: str):
        self.context = context
        self._did = str(uuid.uuid4())
        self.content = []
        self.metadata = {}
        self.annotations = {}
        self.delta_file_name = delta_file_name

    @property
    def did(self):
        return self._did

    # content can be a single Content or a List[Content]
    def add_content(self, content):
        if content:
            if type(content) == list:
                self.content.extend(content)
            else:
                self.content.append(content)

        return self

    def save_string_content(self, string_data: str, name: str, media_type: str, tags: set = None):
        segment = self.context.content_service.put_str(self._did, string_data)
        c = Content(name=name, segments=[segment], media_type=media_type, content_service=self.context.content_service)
        if tags is not None:
            c.add_tags(tags)
        self.content.append(c)
        self.context.saved_content.append(c)
        return self

    def save_byte_content(self, byte_data: bytes, name: str, media_type: str, tags: set = None):
        segment = self.context.content_service.put_bytes(self._did, byte_data)
        c = Content(name=name, segments=[segment], media_type=media_type, content_service=self.context.content_service)
        if tags is not None:
            c.add_tags(tags)
        self.content.append(c)
        self.context.saved_content.append(c)
        return self

    def set_metadata(self, metadata: dict):
        self.metadata = metadata
        return self

    def add_metadata(self, key: str, value: str):
        self.metadata[key] = value
        return self

    def get_segment_names(self):
        segment_names = {}
        for c in self.content:
            segment_names.update(c.get_segment_names())
        return segment_names

    def annotate(self, key: str, value: str):
        self.annotations[key] = value
        return self

    def response(self):
        return {
            'did': self._did,
            'deltaFileName': self.delta_file_name,
            'metadata': self.metadata,
            'content': [content.json() for content in self.content],
            'annotations': self.annotations
        }


class IngressStatusEnum(Enum):
    HEALTHY = 'HEALTHY'
    DEGRADED = 'DEGRADED'
    UNHEALTHY = 'UNHEALTHY'


class IngressResult(Result):
    def __init__(self, context: Context):
        super().__init__('ingress', 'INGRESS', context)
        self.memo = None
        self.ingress_result_items = []
        self.execute_immediate = False
        self.status = IngressStatusEnum.HEALTHY
        self.status_message = None

    def add_item(self, ingress_result_item: IngressResultItem):
        self.ingress_result_items.append(ingress_result_item)
        return self

    def get_segment_names(self):
        segment_names = {}
        for ingress_item in self.ingress_result_items:
            segment_names.update(ingress_item.get_segment_names())
        return segment_names

    def response(self):
        return {
            'memo': self.memo,
            'executeImmediate': self.execute_immediate,
            'ingressItems': [ingress_result_item.response() for ingress_result_item in self.ingress_result_items],
            'status': self.status.value,
            'statusMessage': self.status_message
        }


class TransformResult(Result):
    def __init__(self, context: Context):
        super().__init__('transform', 'TRANSFORM', context)
        self.content = []
        self.annotations = {}
        self.metadata = {}
        self.delete_metadata_keys = []

    # content can be a single Content or a List[Content]
    def add_content(self, content):
        if content:
            if type(content) == list:
                self.content.extend(content)
            else:
                self.content.append(content)

        return self

    def save_string_content(self, string_data: str, name: str, media_type: str, tags: set = None):
        segment = self.context.content_service.put_str(self.context.did, string_data)
        c = Content(name=name, segments=[segment], media_type=media_type, content_service=self.context.content_service)
        if tags is not None:
            c.add_tags(tags)
        self.content.append(c)
        self.context.saved_content.append(c)
        return self

    def save_byte_content(self, byte_data: bytes, name: str, media_type: str, tags: set = None):
        segment = self.context.content_service.put_bytes(self.context.did, byte_data)
        c = Content(name=name, segments=[segment], media_type=media_type, content_service=self.context.content_service)
        if tags is not None:
            c.add_tags(tags)
        self.content.append(c)
        self.context.saved_content.append(c)
        return self

    def set_metadata(self, metadata: dict):
        self.metadata = metadata
        return self

    def add_metadata(self, key: str, value: str):
        self.metadata[key] = value
        return self

    def annotate(self, key: str, value: str):
        self.annotations[key] = value
        return self

    def delete_metadata_key(self, key: str):
        self.delete_metadata_keys.append(key)
        return self

    def get_segment_names(self):
        segment_names = {}
        for c in self.content:
            segment_names.update(c.get_segment_names())
        return segment_names

    def json(self):
        return {
            'did': self.context.did,
            'content': [content.json() for content in self.content],
            'annotations': self.annotations,
            'metadata': self.metadata,
            'deleteMetadataKeys': self.delete_metadata_keys
        }

    def response(self):
        return [self.json()]


class ChildTransformResult(TransformResult):
    delta_file_name: str

    def __init__(self, context: Context, delta_file_name: str = None):
        super().__init__(context.child_context())
        self.delta_file_name = delta_file_name

    def json(self):
        j = super().json()
        j['messages'] = [message.json() for message in self.messages]
        if self.delta_file_name is not None:
            j['name'] = self.delta_file_name
        return j


class TransformResults(Result):
    def __init__(self, context: Context):
        super().__init__('transform', 'TRANSFORM', context)
        self.child_results = []

    def add_result(self, result: ChildTransformResult):
        self.child_results.append(result)
        return self

    def get_segment_names(self):
        segment_names = {}
        for child_result in self.child_results:
            segment_names.update(child_result.get_segment_names())
        return segment_names

    def response(self):
        transform_events = []
        for child_result in self.child_results:
            json_dict = child_result.json()
            transform_events.append(json_dict)
        return transform_events
