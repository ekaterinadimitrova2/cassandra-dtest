import pytest
import logging

from cassandra.protocol import InvalidRequest

from dtest import Tester

since = pytest.mark.since
logger = logging.getLogger(__name__)

VERSION_30 = 'github:ekaterinadimitrova1/CASSANDRA-16063-3.0'
VERSION_311 = 'github:ekaterinadimitrova1/CASSANDRA-16063-3.11'


@pytest.mark.upgrade_test
@since('3.0', max_version='3.11')
class TestDropCompactStorage(Tester):
    """
    Test to verify that dropping compact storage is not possible prior running `nodetool upgradesstables`.
    @CASSANDRA-16063
    """

    def test_drop_compact_storage(self):
        cluster = self.cluster
        cluster.populate(2)
        node1, node2 = cluster.nodelist()
        cluster.set_install_dir(version="2.1.14")
        cluster.start(wait_for_binary_proto=True)

        session = self.patient_cql_connection(node1)
        session.execute(
            "CREATE KEYSPACE drop_compact_storage_test WITH replication = {'class': 'SimpleStrategy', 'replication_factor': '2'};")
        session.execute(
            "CREATE TABLE drop_compact_storage_test.test (a text PRIMARY KEY, b text, c text) WITH COMPACT STORAGE;")

        for i in range(1, 100):
            session.execute(
                "INSERT INTO drop_compact_storage_test.test (a, b, c) VALUES ('{}', '{}', '{}');".format(i, i + 1,
                                                                                                         i + 2))

        logging.debug("Upgrading to current version")
        for node in [node1, node2]:
            node.drain()
            node.watch_log_for("DRAINED")
            node.stop(wait_other_notice=False)

            self.set_node_to_current_version(node)
            node.start(wait_for_binary_proto=True)

        session = self.patient_cql_connection(node1)
        try:
            session.execute("ALTER TABLE drop_compact_storage_test.test DROP COMPACT STORAGE")
            self.fail("No exception has been thrown")
        except InvalidRequest as e:
            assert "Cannot DROP COMPACT STORAGE until all SSTables are upgraded, please run `nodetool upgradesstables` first." in str(e)

        for node in [node1, node2]:
            node.nodetool("upgradesstables")

        session.execute("ALTER TABLE drop_compact_storage_test.test DROP COMPACT STORAGE")

    def test_drop_compact_storage_failure(self):
        cluster = self.cluster
        cluster.populate(2)
        node1, node2 = cluster.nodelist()
        cluster.set_install_dir(version="2.1.14")
        cluster.start(wait_for_binary_proto=True)

        session = self.patient_cql_connection(node1)
        session.execute(
            "CREATE KEYSPACE drop_compact_storage_test WITH replication = {'class': 'SimpleStrategy', 'replication_factor': '2'};")
        session.execute(
            "CREATE TABLE drop_compact_storage_test.test (a text PRIMARY KEY, b text, c text) WITH COMPACT STORAGE;")

        for i in range(1, 100):
            session.execute(
                "INSERT INTO drop_compact_storage_test.test (a, b, c) VALUES ('{}', '{}', '{}');".format(i, i + 1,
                                                                                                         i + 2))

        logging.debug("Upgrading to current version")
        for node in [node1, node2]:
            node.drain()
            node.watch_log_for("DRAINED")
            node.stop(wait_other_notice=False)

            self.set_node_to_current_version(node)
            node.start(wait_for_binary_proto=True)

        session = self.patient_cql_connection(node1)
        try:
            session.execute("ALTER TABLE drop_compact_storage_test.test DROP COMPACT STORAGE")
            self.fail("No exception has been thrown")
        except InvalidRequest as e:
            assert "Cannot DROP COMPACT STORAGE until all SSTables are upgraded, please run `nodetool upgradesstables` first." in str(
                e)

        node1.nodetool("upgradesstables")
        try:
            session.execute("ALTER TABLE drop_compact_storage_test.test DROP COMPACT STORAGE")
            self.fail("No exception has been thrown")
        except InvalidRequest as e:
            assert "Cannot DROP COMPACT STORAGE until all SSTables are upgraded, please run `nodetool upgradesstables` first." in str(
                e)

        node2.nodetool("upgradesstables")
        session.execute("ALTER TABLE drop_compact_storage_test.test DROP COMPACT STORAGE")

        # assert (list(session.execute("SELECT * FROM drop_compact_storage_test.test WHERE a = '10'")) ==
                # [{'a': '10', 'column1': None, 'b': '11', 'c': '12', 'value': None}])

