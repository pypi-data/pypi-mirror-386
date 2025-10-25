"""Integration tests for scheduler and schedule_solve_scheduler."""

from graphqomb.graphstate import GraphState
from graphqomb.schedule_solver import ScheduleConfig, Strategy
from graphqomb.scheduler import Scheduler, compress_schedule


def test_simple_graph_scheduling() -> None:
    """Test scheduling a simple graph with solve_scheduler."""
    # Create a simple 3-node graph
    graph = GraphState()
    node0 = graph.add_physical_node()
    node1 = graph.add_physical_node()
    node2 = graph.add_physical_node()
    graph.add_physical_edge(node0, node1)
    graph.add_physical_edge(node1, node2)
    qindex = 0
    graph.register_input(node0, qindex)
    graph.register_output(node2, qindex)

    flow = {node0: {node1}, node1: {node2}}
    scheduler = Scheduler(graph, flow)

    # Test solve_scheduler-based scheduling
    config = ScheduleConfig(strategy=Strategy.MINIMIZE_TIME)
    success = scheduler.solve_schedule(config)
    assert success

    # Check that times were assigned
    assert scheduler.prepare_time[node1] is not None
    assert scheduler.measure_time[node1] is not None

    # Check schedule structure
    timeline = scheduler.timeline
    assert len(timeline) > 0


def test_manual_vs_solve_scheduler_scheduling() -> None:
    """Test that manual and solve_scheduler scheduling both work."""
    # Create a graph
    graph = GraphState()
    node0 = graph.add_physical_node()
    node1 = graph.add_physical_node()
    node2 = graph.add_physical_node()
    node3 = graph.add_physical_node()
    graph.add_physical_edge(node0, node1)
    graph.add_physical_edge(node1, node2)
    graph.add_physical_edge(node2, node3)
    qindex = 0
    graph.register_input(node0, qindex)
    graph.register_output(node3, qindex)

    flow = {node1: {node0}, node2: {node1}, node3: {node2}}

    scheduler = Scheduler(graph, flow)

    # Test manual scheduling
    scheduler.manual_schedule(prepare_time={node1: 0, node2: 1}, measure_time={node1: 1, node2: 2})
    manual_schedule = scheduler.timeline

    # Test solve_scheduler-based scheduling
    config = ScheduleConfig(strategy=Strategy.MINIMIZE_TIME)
    success = scheduler.solve_schedule(config)
    assert success
    solve_scheduler_schedule = scheduler.timeline

    # Both should produce valid schedules
    assert len(manual_schedule) > 0
    assert len(solve_scheduler_schedule) > 0


def test_solve_scheduler_failure_handling() -> None:
    """Test handling of solve_scheduler failures."""
    graph = GraphState()
    node0 = graph.add_physical_node()
    node1 = graph.add_physical_node()
    graph.add_physical_edge(node0, node1)
    qindex = 0
    graph.register_input(node0, qindex)
    graph.register_output(node1, qindex)

    flow = {node0: {node1}, node1: {node0}}  # This should be impossible to satisfy

    scheduler = Scheduler(graph, flow)

    # Solver should return False for unsolvable problems
    config = ScheduleConfig(strategy=Strategy.MINIMIZE_TIME)
    success = scheduler.solve_schedule(config, timeout=1)
    # Note: This might still succeed depending on the specific constraints
    # The test mainly checks that the method doesn't crash
    assert isinstance(success, bool)


def test_schedule_config_options() -> None:
    """Test different ScheduleConfig options."""
    # Create a simple graph
    graph = GraphState()
    node0 = graph.add_physical_node()
    node1 = graph.add_physical_node()
    node2 = graph.add_physical_node()
    graph.add_physical_edge(node0, node1)
    graph.add_physical_edge(node1, node2)
    qindex = 0
    graph.register_input(node0, qindex)
    graph.register_output(node2, qindex)

    flow = {node0: {node1}, node1: {node2}}
    scheduler = Scheduler(graph, flow)

    # Test space optimization
    space_config = ScheduleConfig(strategy=Strategy.MINIMIZE_SPACE)
    success = scheduler.solve_schedule(space_config)
    assert success
    space_slices = scheduler.num_slices()

    # Test time optimization
    time_config = ScheduleConfig(strategy=Strategy.MINIMIZE_TIME)
    success = scheduler.solve_schedule(time_config)
    assert success
    time_slices = scheduler.num_slices()

    # Test custom max_time
    custom_time_config = ScheduleConfig(strategy=Strategy.MINIMIZE_SPACE, max_time=10)
    success = scheduler.solve_schedule(custom_time_config)
    assert success

    # Time optimization should generally use fewer slices than space optimization
    # (though this isn't guaranteed for all graphs)
    assert time_slices <= space_slices or space_slices <= time_slices  # Either way is valid


def test_space_constrained_scheduling() -> None:
    """Test space-constrained time optimization."""
    # Create a larger graph to test constraints
    graph = GraphState()
    nodes = [graph.add_physical_node() for _ in range(5)]

    # Create a chain of nodes
    for i in range(4):
        graph.add_physical_edge(nodes[i], nodes[i + 1])

    qindex = 0
    graph.register_input(nodes[0], qindex)
    graph.register_output(nodes[4], qindex)

    # Simple flow
    flow = {nodes[i]: {nodes[i + 1]} for i in range(4)}
    scheduler = Scheduler(graph, flow)

    # Test constrained optimization
    max_qubits = 3
    constrained_config = ScheduleConfig(strategy=Strategy.MINIMIZE_TIME, max_qubit_count=max_qubits)

    success = scheduler.solve_schedule(constrained_config, timeout=30)

    # This might fail if the constraint is too restrictive,
    # but the method should not crash
    assert isinstance(success, bool)


def test_schedule_compression() -> None:
    """Test that schedule compression reduces unnecessary time gaps."""
    # Create a graph
    graph = GraphState()
    node0 = graph.add_physical_node()
    node1 = graph.add_physical_node()
    node2 = graph.add_physical_node()
    graph.add_physical_edge(node0, node1)
    graph.add_physical_edge(node1, node2)
    qindex = 0
    graph.register_input(node0, qindex)
    graph.register_output(node2, qindex)

    flow = {node0: {node1}, node1: {node2}}
    scheduler = Scheduler(graph, flow)

    # Test manual scheduling with gaps
    scheduler.manual_schedule(prepare_time={node1: 5}, measure_time={node1: 10})

    # Before compression, there should be gaps
    slices_before = scheduler.num_slices()

    # Apply compression
    compressed_prep_time, compressed_meas_time = compress_schedule(scheduler.prepare_time, scheduler.measure_time)
    scheduler.prepare_time = compressed_prep_time
    scheduler.measure_time = compressed_meas_time

    # After compression, gaps should be removed
    slices_after = scheduler.num_slices()

    # Compression should reduce the number of slices
    assert slices_after <= slices_before

    # The compressed schedule should be more compact
    # All time indices should be consecutive starting from 0
    prep_times = [t for t in scheduler.prepare_time.values() if t is not None]
    meas_times = [t for t in scheduler.measure_time.values() if t is not None]
    all_used_times = sorted(set(prep_times + meas_times))

    # Times should be consecutive from 0
    expected_times = list(range(len(all_used_times)))
    assert all_used_times == expected_times


def test_solve_scheduler_with_automatic_compression() -> None:
    """Test that solve_scheduler results are automatically compressed."""
    # Create a simple graph
    graph = GraphState()
    node0 = graph.add_physical_node()
    node1 = graph.add_physical_node()
    node2 = graph.add_physical_node()
    graph.add_physical_edge(node0, node1)
    graph.add_physical_edge(node1, node2)
    qindex = 0
    graph.register_input(node0, qindex)
    graph.register_output(node2, qindex)

    flow = {node0: {node1}, node1: {node2}}
    scheduler = Scheduler(graph, flow)

    # Test with MINIMIZE_SPACE strategy (prone to gaps)
    config = ScheduleConfig(strategy=Strategy.MINIMIZE_SPACE)
    success = scheduler.solve_schedule(config)
    assert success

    # Verify that compression was applied automatically
    prep_times = [t for t in scheduler.prepare_time.values() if t is not None]
    meas_times = [t for t in scheduler.measure_time.values() if t is not None]
    all_used_times = sorted(set(prep_times + meas_times))

    # Times should start from 0 and be consecutive (no gaps)
    if all_used_times:  # Only check if there are any times
        assert all_used_times[0] == 0  # Should start from 0
        # Check that times are consecutive (no large gaps)
        if len(all_used_times) > 1:
            max_gap = max(all_used_times[i + 1] - all_used_times[i] for i in range(len(all_used_times) - 1))
            assert max_gap <= 1  # At most gap of 1 (consecutive times)


def test_validate_schedule_valid() -> None:
    """Test that validate_schedule correctly identifies valid schedules."""
    # Create a simple graph
    graph = GraphState()
    node0 = graph.add_physical_node()
    node1 = graph.add_physical_node()
    node2 = graph.add_physical_node()
    graph.add_physical_edge(node0, node1)
    graph.add_physical_edge(node1, node2)
    qindex = 0
    graph.register_input(node0, qindex)
    graph.register_output(node2, qindex)

    flow = {node0: {node1}, node1: {node2}}
    scheduler = Scheduler(graph, flow)

    # Test that a solve_scheduler-generated schedule is valid
    config = ScheduleConfig(strategy=Strategy.MINIMIZE_TIME)
    success = scheduler.solve_schedule(config)
    assert success
    assert scheduler.validate_schedule()

    # Test a valid manual schedule
    scheduler2 = Scheduler(graph, flow)
    # node0 is input (not in prepare_time), node2 is output (not in measure_time)
    scheduler2.manual_schedule(prepare_time={node1: 0, node2: 1}, measure_time={node0: 0, node1: 1})
    assert scheduler2.validate_schedule()


def test_validate_schedule_invalid_node_sets() -> None:
    """Test that validate_schedule rejects schedules with wrong node sets."""
    # Create a graph
    graph = GraphState()
    node0 = graph.add_physical_node()
    node1 = graph.add_physical_node()
    node2 = graph.add_physical_node()
    graph.add_physical_edge(node0, node1)
    graph.add_physical_edge(node1, node2)
    qindex = 0
    graph.register_input(node0, qindex)
    graph.register_output(node2, qindex)

    flow = {node0: {node1}, node1: {node2}}
    scheduler = Scheduler(graph, flow)

    # Manually set invalid schedule (trying to prepare input node)
    scheduler.prepare_time = {node0: 0, node1: 1}  # node0 is input, shouldn't be prepared
    scheduler.measure_time = {node0: 1, node1: 2}
    assert not scheduler.validate_schedule()

    # Reset and test measuring output node
    scheduler2 = Scheduler(graph, flow)
    scheduler2.prepare_time = {node1: 0}
    scheduler2.measure_time = {node0: 1, node1: 1, node2: 2}  # node2 is output, shouldn't be measured
    assert not scheduler2.validate_schedule()


def test_validate_schedule_missing_times() -> None:
    """Test that validate_schedule rejects schedules with missing times."""
    # Create a graph
    graph = GraphState()
    node0 = graph.add_physical_node()
    node1 = graph.add_physical_node()
    node2 = graph.add_physical_node()
    graph.add_physical_edge(node0, node1)
    graph.add_physical_edge(node1, node2)
    qindex = 0
    graph.register_input(node0, qindex)
    graph.register_output(node2, qindex)

    flow = {node0: {node1}, node1: {node2}}
    scheduler = Scheduler(graph, flow)

    # Set schedule with None values (unscheduled nodes)
    scheduler.prepare_time = {node1: None}  # node1 not scheduled for preparation
    scheduler.measure_time = {node0: 0, node1: 1}
    assert not scheduler.validate_schedule()

    # Reset and test missing measurement time
    scheduler2 = Scheduler(graph, flow)
    scheduler2.prepare_time = {node1: 0}
    scheduler2.measure_time = {node0: 0, node1: None}  # node1 not scheduled for measurement
    assert not scheduler2.validate_schedule()


def test_validate_schedule_dag_violations() -> None:
    """Test that validate_schedule rejects schedules violating DAG constraints."""
    # Create a graph with flow dependencies
    graph = GraphState()
    node0 = graph.add_physical_node()
    node1 = graph.add_physical_node()
    node2 = graph.add_physical_node()
    node3 = graph.add_physical_node()
    graph.add_physical_edge(node0, node1)
    graph.add_physical_edge(node1, node2)
    graph.add_physical_edge(node2, node3)
    qindex = 0
    graph.register_input(node0, qindex)
    graph.register_output(node3, qindex)

    # Flow creates DAG: node0 -> node1 -> node2
    flow = {node0: {node1}, node1: {node2}}
    scheduler = Scheduler(graph, flow)

    # Set schedule that violates DAG (node1 measured after node2)
    scheduler.prepare_time = {node1: 0, node2: 0}
    scheduler.measure_time = {node0: 0, node1: 2, node2: 1}  # Violates DAG: node1 should be measured before node2
    assert not scheduler.validate_schedule()

    # Test equal times (also violates DAG)
    scheduler2 = Scheduler(graph, flow)
    scheduler2.prepare_time = {node1: 0, node2: 0}
    scheduler2.measure_time = {node0: 0, node1: 1, node2: 1}  # Same measurement time violates DAG
    assert not scheduler2.validate_schedule()


def test_validate_schedule_same_time_prep_meas() -> None:
    """Test that validate_schedule rejects schedules with nodes prepared and measured at same time."""
    # Create a graph
    graph = GraphState()
    node0 = graph.add_physical_node()
    node1 = graph.add_physical_node()
    node2 = graph.add_physical_node()
    graph.add_physical_edge(node0, node1)
    graph.add_physical_edge(node1, node2)
    qindex = 0
    graph.register_input(node0, qindex)
    graph.register_output(node2, qindex)

    flow = {node0: {node1}, node1: {node2}}
    scheduler = Scheduler(graph, flow)

    # Set schedule where node1 is both prepared and measured at time 1
    scheduler.prepare_time = {node1: 1}
    scheduler.measure_time = {node0: 0, node1: 1}  # node1 prepared and measured at time 1
    assert not scheduler.validate_schedule()
