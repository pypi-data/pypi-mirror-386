# coding=utf-8
# Copyright (c) 2025 Jifeng Wu
# Licensed under the MIT License. See LICENSE file in the project root for full license information.
from __future__ import print_function

from collections import OrderedDict

from numpy import array, dot, ndarray
from numpy.linalg import norm
from retrieve_sentence_embeddings import retrieve_sentence_embeddings
from typing import Iterable, List, Mapping, Text, TypeVar, Tuple, Union
from unicode_raw_input import unicode_raw_input

K = TypeVar('K')


class TransientInMemorySemanticSearchEngine(Mapping[K, ndarray]):
    __slots__ = (
        'api_key',
        'base_url',
        'model',
        'keys_to_indices',
        'normalized_document_embeddings'
    )

    def __new__(
            cls,
            api_key,  # type: Text
            base_url,  # type: Text
            model,  # type: Text
            key_value_mapping_or_key_value_pairs,  # type: Union[Mapping[K, Text], Iterable[Tuple[K, Text]]]
            **kwargs
    ):
        """
        Keys and document order/index alignment:

        - We construct an OrderedDict 'keys_to_indices' and a list 'documents' so that,
          for any key, keys_to_indices[key] gives the index in the 'documents' list at which
          this key's document appears (and, later, embedding in the array).
        - If duplicate keys are encountered (either in the main iterable or because of **kwargs),
          the document for that key is overwritten at its existing index.
        - As a result, at the end of construction, the i-th item in 'documents' always corresponds
          to the key at the i-th position of keys_to_indices, and keys_to_indices[key]
          gives the proper matching document index for each key.
        - This alignment is crucial, as it ensures semantic search results are returned with the right keys.
        """
        keys_to_indices = OrderedDict()
        documents = []

        if isinstance(key_value_mapping_or_key_value_pairs, Mapping):
            for key, value in key_value_mapping_or_key_value_pairs.items():
                if not isinstance(value, Text):
                    raise ValueError('Values must be Text')
                keys_to_indices[key] = len(keys_to_indices)
                documents.append(value)
        elif isinstance(key_value_mapping_or_key_value_pairs, Iterable):
            for key_value_pair in key_value_mapping_or_key_value_pairs:
                if not isinstance(key_value_pair, Tuple) or len(key_value_pair) != 2:
                    raise ValueError(
                        'key_value_mapping_or_key_value_pairs must be Mapping[K, Text] or Iterable[Tuple[K, Text]]'
                    )
                key, value = key_value_pair
                if not isinstance(value, Text):
                    raise ValueError('Values must be Text')
                if key not in keys_to_indices:
                    keys_to_indices[key] = len(keys_to_indices)
                    documents.append(value)
                else:
                    index = keys_to_indices[key]
                    documents[index] = value
        else:
            raise ValueError(
                'key_value_mapping_or_key_value_pairs must be Mapping[K, Text] or Iterable[Tuple[K, Text]]'
            )

        for key, value in kwargs.items():
            if not isinstance(value, Text):
                raise ValueError('Values must be Text')
            if key not in keys_to_indices:
                keys_to_indices[key] = len(keys_to_indices)
                documents.append(value)
            else:
                index = keys_to_indices[key]
                documents[index] = value

        normalized_document_embeddings = array(
            retrieve_sentence_embeddings(
                api_key, base_url, model, documents
            )
        )

        normalized_document_embeddings /= norm(normalized_document_embeddings, axis=1, keepdims=True)

        self = super(TransientInMemorySemanticSearchEngine, cls).__new__(cls)
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.keys_to_indices = keys_to_indices
        self.normalized_document_embeddings = normalized_document_embeddings
        return self

    def __call__(self, sentence):
        # type: (Text) -> List[Tuple[float, K]]
        if not isinstance(sentence, Text):
            raise ValueError('sentence must be Text')

        normalized_sentence_embedding = array(
            retrieve_sentence_embeddings(
                self.api_key, self.base_url, self.model, [sentence]
            )[0]
        )

        normalized_sentence_embedding /= norm(normalized_sentence_embedding)

        cosine_similarities = dot(self.normalized_document_embeddings, normalized_sentence_embedding)

        results = list(zip(map(float, cosine_similarities), self.keys_to_indices.keys()))
        results.sort(reverse=True)

        return results

    def __contains__(self, key):
        # type: (K) -> bool
        return key in self.keys_to_indices

    def __getitem__(self, key):
        # type: (K) -> ndarray
        return self.normalized_document_embeddings[self.keys_to_indices[key]]

    def __iter__(self):
        # type: () -> Iterable[K]
        return iter(self.keys_to_indices)

    def __len__(self):
        # type: () -> int
        return len(self.keys_to_indices)


if __name__ == '__main__':
    import argparse
    import codecs
    import json


    def main():
        parser = argparse.ArgumentParser()

        # Add arguments
        parser.add_argument(
            '-k', '--api-key',
            type=str,
            required=True,
            help='API key'
        )

        parser.add_argument(
            '-u', '--base-url',
            type=str,
            required=True,
            help='Base URL'
        )

        parser.add_argument(
            '-m', '--model',
            type=str,
            required=True,
            help='Model name'
        )

        parser.add_argument(
            '-j', '--key-value-json',
            metavar='KEY_VALUE_JSON',
            type=str,
            required=False,
            help='A JSON object mapping keys to textual values representing a document collection.'
        )

        args = parser.parse_args()

        with codecs.open(args.key_value_json, 'r', encoding='utf-8') as f:
            key_value_json = json.load(f)

        if (
                not isinstance(key_value_json, Mapping)
                or not all(isinstance(value, Text) for value in key_value_json.values())
        ):
            raise ValueError('KEY_VALUE_JSON must be a JSON object with textual values')

        engine = TransientInMemorySemanticSearchEngine(
            api_key=args.api_key,
            base_url=args.base_url,
            model=args.model,
            key_value_mapping_or_key_value_pairs=key_value_json
        )

        while True:
            query = unicode_raw_input(u'Enter a query: ')
            results = engine(query)
            print(u'score,key')
            for score, key in results:
                print(u'%.4f,%s' % (score, json.dumps(key)))


    main()
