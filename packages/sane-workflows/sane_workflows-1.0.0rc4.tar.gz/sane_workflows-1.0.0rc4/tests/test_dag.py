import unittest

from sane.dag import DAG
from sane.dagvis import visualize as dagvis


class DagTests( unittest.TestCase ):

  def setUp( self ):
    self.dag = DAG()

  def dag_valid( self, nodes, valid ):
    self.assertTrue( valid )
    for node in nodes:
      self.assertIn( node, self.dag._nodes )
    self.assertEqual( len( nodes ), len( self.dag._nodes ) )

  def dag_invalid( self, nodes, valid ):
    self.assertFalse( valid )
    # This cannot be tested like so since all nodes may be problematic
    # self.assertNotEqual( len( nodes ), len( self.dag._nodes ) )

  def validate_traversal( self, traversal_list, expected ):
    step     = 0
    while len( traversal_list ) > 0:
      nodes = self.dag.get_next_nodes( traversal_list )
      for node in nodes:
        self.assertIn( node, expected[step] )
        expected[step].remove( node )

        self.assertNotIn( node, traversal_list )
        self.dag.node_complete( node, traversal_list )
      step += 1

    # All expected should have been visited in this walk
    self.assertEqual( traversal_list, {} )
    for node_list in expected:
      self.assertEqual( node_list, [] )

  def test_dag_no_nodes( self ):
    """A valid DAG consisting of no nodes"""
    nodes, valid = self.dag.topological_sort()
    self.dag_valid( nodes, valid )
    self.assertEqual( nodes, [] )

  def test_dag_single_node( self ):
    """A valid DAG consisting of a single node"""
    self.dag.add_node( "a" )

    nodes, valid = self.dag.topological_sort()
    self.dag_valid( nodes, valid )
    self.assertEqual( nodes, [ "a" ] )

  def test_dag_isolated_nodes( self ):
    """A valid DAG consisting of multiple isolated nodes"""
    self.dag.add_node( "a" )
    self.dag.add_node( "b" )
    self.dag.add_node( "c" )
    self.dag.add_node( "d" )

    nodes, valid = self.dag.topological_sort()
    self.dag_valid( nodes, valid )
    self.assertEqual( nodes, [ "a", "b", "c", "d" ] )

  def test_dag_2node_acyclic( self ):
    """A valid DAG consisting of 2 nodes, one pointing to the other"""
    self.dag.add_node( "a" )
    self.dag.add_node( "b" )
    # this sets up a -> b where b is dependent (child) on a (parent)
    self.dag.add_edge( "a", "b" )

    nodes, valid = self.dag.topological_sort()
    self.dag_valid( nodes, valid )
    self.assertEqual( nodes, [ "a", "b" ] )

  def test_dag_2node_acyclic_via_edge( self ):
    """A valid DAG consisting of 2 nodes, one pointing to the other

    This does not individually create the nodes and then connect them,
    instead creating the nodes via the add_edge() command directly.

    The result should be something identical to the create-then-link DAG
    """
    # this sets up a -> b where b is dependent (child) on a (parent)
    self.dag.add_edge( "a", "b" )

    nodes, valid = self.dag.topological_sort()
    self.dag_valid( nodes, valid )
    self.assertEqual( nodes, [ "a", "b" ] )

  def test_dag_2node_cyclic( self ):
    """An invalid DAG consisting of 2 nodes pointing to each other creating a cycle"""
    self.dag.add_node( "a" )
    self.dag.add_node( "b" )
    # this sets up a -> b where b is dependent (child) on a (parent)
    self.dag.add_edge( "a", "b" )
    # this creates the simplest cycle
    self.dag.add_edge( "b", "a" )

    nodes, valid = self.dag.topological_sort()
    self.dag_invalid( nodes, valid )
    # nodes should now be equal to the potentially bad nodes
    self.assertEqual( nodes, [ "a", "b" ] )

  def test_dag_5node_acyclic_single_entry_single_end( self ):
    """A valid DAG consisting of 5 nodes with one start node and one end node

    The single start node has an in-degree of zero and the path to the final
    node is fully reduced and requires traversal to all other nodes:
          a
          v
          b
        __|__
      v      v
      c      d
      |______|
          |
          v
          e
    """
    # This also tests creation via edge addition
    self.dag.add_edge( "a", "b" )
    self.dag.add_edge( "b", "c" )
    self.dag.add_edge( "b", "d" )
    self.dag.add_edge( "c", "e" )
    self.dag.add_edge( "d", "e" )

    nodes, valid = self.dag.topological_sort()
    self.dag_valid( nodes, valid )
    self.assertEqual( nodes, [ "a", "b", "c", "d", "e" ] )

  def test_dag_5node_acyclic_traversal_to_end( self ):
    """A valid DAG consisting of 5 nodes and testing traversal to the end

    The single start node has an in-degree of zero and the path to the final
    node is fully reduced and requires traversal to all other nodes:
          a
          v
          b
        __|__
      v      v
      c      d
      |______|
          |
          v
          e

    From here, the traversal to "e" should consist of a -> b -> [c, d] -> e
    """
    # Start from this test
    self.test_dag_5node_acyclic_single_entry_single_end()

    traversal_list = self.dag.traversal_to( [ "e" ] )
    # The traversal list is a record of all levels that must be traversed and
    # which nodes in that level to visited. The flattened version should have
    # the total nodes
    print( traversal_list )
    self.assertEqual( len( traversal_list ), 4 )
    self.assertEqual( len( [ node for node_list in traversal_list for node in node_list ] ), len( self.dag._nodes ) )

  def test_dag_5node_acyclic_traversal_list( self ):
    """A valid DAG consisting of 5 nodes and walking the traversal one node at a time

    The single start node has an in-degree of zero and the path to the final
    node is fully reduced and requires traversal to all other nodes:
          a
          v
          b
        __|__
      v      v
      c      d
      |______|
          |
          v
          e

    From here, the traversal to "e" should consist of a -> b -> [c, d] -> e
    Thus, a walk of the traversal using traversal_list() should yield:
    a then b then [c or d] then [d or c, whichever did not yet run] then e
    """
    # Start from this test
    self.test_dag_5node_acyclic_traversal_to_end()
    # Get traversal_list
    traversal_list = self.dag.traversal_list( [ "e" ] )
    self.assertEqual( len( traversal_list ), len( self.dag._nodes ) )

    expected = self.dag.traversal_to( [ "e" ] )
    self.validate_traversal( traversal_list, expected )

  def test_dag_multinode_entry_multinode_end_partial( self ):
    """A valid DAG consisting of multiple zero in-degree nodes

    This test will have multiple required in-degree nodes but also multiple
    ending nodes such that a traversal to one results in a partial traversal
    start -> stop
        b - d
    a <   /   > l => requires [a,f,i], [b,c,g], [d,e]
        c - e
    f <   /   > m => requires [a,f,i], [c,g,j], [e,h]
        g - h
    i <   /   > n => requires [f,i], [g,j], [h,k]
        j - k
    """
    self.dag.add_edge( "d", "l" )
    self.dag.add_edge( "e", "l" )
    self.dag.add_edge( "e", "m" )
    self.dag.add_edge( "h", "m" )
    self.dag.add_edge( "h", "n" )
    self.dag.add_edge( "k", "n" )

    self.dag.add_edge( "b", "d" )
    self.dag.add_edge( "c", "d" )
    self.dag.add_edge( "c", "e" )
    self.dag.add_edge( "g", "e" )
    self.dag.add_edge( "g", "h" )
    self.dag.add_edge( "j", "h" )
    self.dag.add_edge( "j", "k" )

    self.dag.add_edge( "a", "b" )
    self.dag.add_edge( "a", "c" )
    self.dag.add_edge( "f", "c" )
    self.dag.add_edge( "f", "g" )
    self.dag.add_edge( "i", "g" )
    self.dag.add_edge( "i", "j" )

    traversal_list = self.dag.traversal_list( [ "l" ] )
    self.assertNotEqual( len( traversal_list ), len( self.dag._nodes ) )

    expected = [ [ "a", "f", "i" ], [ "b", "c", "g" ], [ "d", "e" ], [ "l" ] ]
    self.validate_traversal( traversal_list, expected )

    traversal_list = self.dag.traversal_list( [ "m" ] )
    self.assertNotEqual( len( traversal_list ), len( self.dag._nodes ) )

    expected = [ [ "a", "f", "i" ], [ "c", "g", "j" ], [ "e", "h" ], [ "m" ] ]
    self.validate_traversal( traversal_list, expected )

    traversal_list = self.dag.traversal_list( [ "n" ] )
    self.assertNotEqual( len( traversal_list ), len( self.dag._nodes ) )

    expected = [ [ "f", "i" ], [ "g", "j" ], [ "h", "k" ], [ "n" ] ]
    self.validate_traversal( traversal_list, expected )

  def test_dag_visualize( self ):
    self.test_dag_multinode_entry_multinode_end_partial()
    print( dagvis( self.dag, [ "l", "m", "n" ] ) )
    self.dag.add_edge( 0, 1 )
    self.dag.add_edge( 0, 2 )
    self.dag.add_edge( 0, 4 )
    self.dag.add_edge( 1, 2 )
    self.dag.add_edge( 1, 3 )
    self.dag.add_edge( 1, 5 )
    self.dag.add_edge( 2, 3 )
    self.dag.add_edge( 2, 4 )
    print( dagvis( self.dag, [ 3, 4, 5 ] ) )
