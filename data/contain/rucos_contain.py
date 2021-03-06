import json
from typing import Optional, List, Set
from itertools import islice

from ..types.rucos.parsed import RucosParsedParagraph, RucosParsedCandidate
from ..types.rucos.raw import RucosRawParagraph, RucosRawEntity, RucosRawQuery, RucosRawPassage


class RucosDataContainer:
    def __init__(
            self,
            path: str,
            has_labels: bool = True,
            nrows: Optional[int] = None,
            start_row=0,
            text_idxs: List[int] = None,
            query_placeholder_union_mode="replace",
            extend_entities_with_answers: bool = False
    ):
        self.path = path
        self.nrows = nrows
        self.has_labels = has_labels
        self.start_row = start_row
        self.text_idxs = text_idxs
        self.extend_entities_with_answers = extend_entities_with_answers

        if query_placeholder_union_mode not in ["replace", "concatenate"]:
            raise ValueError(query_placeholder_union_mode)
        self.query_placeholder_union_mode = query_placeholder_union_mode

    def get_data(self) -> List[RucosParsedParagraph]:
        result: List[RucosParsedParagraph] = []
        with open(self.path) as f:
            if self.text_idxs is None:
                if self.nrows is None:
                    iterable = islice(f, self.start_row, None)
                else:
                    iterable = islice(f, self.start_row, self.start_row + self.nrows)
                for line in iterable:
                    p: RucosRawParagraph = json.loads(line)
                    self._fill_missed_data(p)
                    result.append(self._parse_paragraph(p))

            # get by idxs
            else:
                lines = f.readlines()
                for idx in self.text_idxs:
                    p: RucosRawParagraph = json.loads(lines[idx])   
                    self._fill_missed_data(p)
                    result.append(self._parse_paragraph(p))
        return result

    def _fill_missed_data(self, p: RucosRawParagraph) -> None:
        for entity in p['passage']['entities']:
            entity['text'] = p['passage']['text'][entity['start']:entity['end']]

    def _parse_paragraph(self, p: RucosRawParagraph) -> RucosParsedParagraph:
        if self.extend_entities_with_answers:
            candidates = p['passage']['entities'] + p['qas'][0]['answers']
        else:
            candidates = p['passage']['entities']
        candidates = self._filter_duplicate_entities(candidates)
        return RucosParsedParagraph(
            text1=p['passage']['text'],
            idx=p['idx'],
            candidates=[self._parse_candidate(e, p['qas'][0], p['passage']) for e in candidates]
        )

    def _filter_duplicate_entities(self, entities: List[RucosRawEntity]) -> List[RucosRawEntity]:
        filtered_entities: List[RucosRawEntity] = []
        encountered_answers: Set[str] = set()
        for entity in entities:
            if entity['text'] not in encountered_answers:
                filtered_entities.append(entity)
                encountered_answers.add(entity['text'])
        return filtered_entities

    def _parse_candidate(
            self,
            entity: RucosRawEntity,
            query: RucosRawQuery,
            passage: RucosRawPassage
    ) -> RucosParsedCandidate:
        placeholder = passage['text'][entity['start']:entity['end']]
        if self.has_labels:
            filtered_answers = self._filter_duplicate_entities(query['answers'])
            is_answer = any(ans['text'] == entity['text'] for ans in filtered_answers)
            label = 1 if is_answer else 0
        else:
            label = None


        if self.query_placeholder_union_mode == "replace":
            text2 = query['query'].replace(
                '@placeholder',
                placeholder,
                1)
        else:
            text2 = placeholder + " " + query["query"]

        return RucosParsedCandidate(
            text2=text2,
            label=label,
            start_char=entity['start'],
            end_char=entity['end'],
            placeholder=placeholder
        )
