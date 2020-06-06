# -*- coding: utf-8 -*-
# Copyright 2020 The Matrix.org Foundation C.I.C.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from synapse.storage.database import (
    make_tuple_comparison_clause,
    make_in_list_sql_clause,
    make_multi_column_in_list_sql_clause,
)
from synapse.storage.engines import BaseDatabaseEngine

from tests import unittest


def _stub_db_engine(**kwargs) -> BaseDatabaseEngine:
    # returns a DatabaseEngine, circumventing the abc mechanism
    # any kwargs are set as attributes on the class before instantiating it
    t = type(
        "TestBaseDatabaseEngine",
        (BaseDatabaseEngine,),
        dict(BaseDatabaseEngine.__dict__),
    )
    # defeat the abc mechanism
    t.__abstractmethods__ = set()
    for k, v in kwargs.items():
        setattr(t, k, v)
    return t(None, None)


class TupleComparisonClauseTestCase(unittest.TestCase):
    def test_native_tuple_comparison(self):
        db_engine = _stub_db_engine(supports_tuple_comparison=True)
        clause, args = make_tuple_comparison_clause(db_engine, [("a", 1), ("b", 2)])
        self.assertEqual(clause, "(a,b) > (?,?)")
        self.assertEqual(args, [1, 2])

    def test_emulated_tuple_comparison(self):
        db_engine = _stub_db_engine(supports_tuple_comparison=False)
        clause, args = make_tuple_comparison_clause(
            db_engine, [("a", 1), ("b", 2), ("c", 3)]
        )
        self.assertEqual(
            clause, "(a >= ? AND (a > ? OR (b >= ? AND (b > ? OR c > ?))))"
        )
        self.assertEqual(args, [1, 1, 2, 2, 3])


class InListClauseTestCase(unittest.TestCase):
    def test_any_list(self):
        db_engine = _stub_db_engine(supports_using_any_list=True)
        clause, args = make_in_list_sql_clause(db_engine, "a", [1, 2, 3, 4])
        self.assertEqual(clause, "a = ANY(?)")
        self.assertEqual(args, [[1, 2, 3, 4]])

    def test_in_list(self):
        db_engine = _stub_db_engine(supports_using_any_list=False)
        clause, args = make_in_list_sql_clause(db_engine, "a", [1, 2, 3, 4])
        self.assertEqual(clause, "a IN (?,?,?,?)")
        self.assertEqual(args, [1, 2, 3, 4])


class MultiColumnInListClauseTestCase(unittest.TestCase):
    # def test_any_tuple_list(self):
    #     db_engine = _stub_db_engine(
    #         supports_tuple_comparison=True, supports_using_any_list=True,
    #     )
    #     clause, args = make_multi_column_in_list_sql_clause(
    #         db_engine, ("a", "b"), [(1, 2), (3, 4)],
    #     )
    #     self.assertEqual(clause, "(a,b) = ANY(?)")
    #     self.assertEqual(args, [[(1, 2), (3, 4)]])

    def test_native_multi_column_in_list(self):
        db_engine = _stub_db_engine(supports_tuple_comparison=True)
        clause, args = make_multi_column_in_list_sql_clause(
            db_engine, ("a", "b"), [(1, 2), (3, 4)],
        )
        self.assertEqual(clause, "(a,b) IN (VALUES (?,?),(?,?))")
        self.assertEqual(args, [1, 2, 3, 4])

    def test_emulated_multi_column_in_list(self):
        db_engine = _stub_db_engine(supports_tuple_comparison=False)
        clause, args = make_multi_column_in_list_sql_clause(
            db_engine, ("a", "b"), [(1, 2), (3, 4)],
        )
        self.assertEqual(clause, "((a = ? AND b = ?) OR (a = ? AND b = ?))")
        self.assertEqual(args, [1, 2, 3, 4])
