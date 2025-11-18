# apps/core/utils/uom_utils.py
"""
Utilities for Unit of Measure (UoM) conversion chains

⭐ NEW Week 2 Day 3

Provides ConversionChain calculator for converting between units
through intermediate steps (e.g., mg → g → kg → ton)
"""

from decimal import Decimal
from collections import defaultdict, deque
from typing import List, Dict, Optional, Tuple
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class ConversionChain:
    """
    Helper class for calculating conversion chains between UoM units.

    ⭐ NEW Week 2 Day 3

    Uses Graph theory (BFS) to find conversion paths between units
    within the same UoM Group.

    Example:
        mg → g → kg → ton
        1000 mg = 1 g = 0.001 kg = 0.000001 ton

    Usage:
        chain = ConversionChain(weight_group, company)
        result = chain.calculate(mg, ton, Decimal('5000000'))
        # result = Decimal('0.005')  # 5 million mg = 0.005 ton
    """

    def __init__(self, uom_group, company):
        """
        Initialize conversion chain calculator for a UoM Group.

        Args:
            uom_group: UoMGroup instance
            company: Company instance for filtering conversions
        """
        self.group = uom_group
        self.company = company
        self.graph = defaultdict(list)  # adjacency list
        self.conversions = {}  # (from_uom_id, to_uom_id) -> factor
        self._build_graph()

    def _build_graph(self):
        """
        Build conversion graph for the group.

        Creates a directed graph where:
        - Nodes: UoM units in the group
        - Edges: Conversions with factors

        Graph structure:
            {
                from_uom_id: [(to_uom_id, conversion_factor), ...],
                ...
            }
        """
        from apps.core.models import UoMConversion

        # Get all conversions for units in this group
        conversions = UoMConversion.objects.filter(
            company=self.company,
            from_uom__uom_group=self.group,
            item__isnull=True,  # Only global conversions
            variant__isnull=True,
            is_active=True
        ).select_related('from_uom')

        # Build bidirectional graph
        for conv in conversions:
            from_id = conv.from_uom.id
            to_id = self.group.base_uom.id if self.group.base_uom else None

            if to_id:
                # Forward: from_uom → base_uom
                self.graph[from_id].append((to_id, conv.conversion_factor))
                self.conversions[(from_id, to_id)] = conv.conversion_factor

                # Backward: base_uom → from_uom (inverse factor)
                inverse_factor = Decimal('1') / conv.conversion_factor
                self.graph[to_id].append((from_id, inverse_factor))
                self.conversions[(to_id, from_id)] = inverse_factor

    def find_path(self, from_uom, to_uom) -> Optional[List[Tuple[int, Decimal]]]:
        """
        Find conversion path from source to target UoM using BFS.

        Args:
            from_uom: Source UnitOfMeasure instance
            to_uom: Target UnitOfMeasure instance

        Returns:
            List of (uom_id, cumulative_factor) tuples representing the path,
            or None if no path exists

        Example:
            path = chain.find_path(mg, ton)
            # [(mg.id, 1), (g.id, 0.001), (kg.id, 0.000001), (ton.id, 0.000000001)]
        """
        if from_uom.id == to_uom.id:
            return [(from_uom.id, Decimal('1'))]

        # BFS to find shortest path
        queue = deque([(from_uom.id, Decimal('1'), [from_uom.id])])
        visited = {from_uom.id}

        while queue:
            current_id, cumulative_factor, path = queue.popleft()

            # Check neighbors
            for next_id, edge_factor in self.graph.get(current_id, []):
                if next_id in visited:
                    continue

                new_factor = cumulative_factor * edge_factor
                new_path = path + [next_id]

                # Found target
                if next_id == to_uom.id:
                    # Return path with cumulative factors
                    result = []
                    factor = Decimal('1')
                    for i, uom_id in enumerate(new_path):
                        result.append((uom_id, factor))
                        if i < len(new_path) - 1:
                            factor = factor * self.conversions.get(
                                (new_path[i], new_path[i+1]),
                                Decimal('1')
                            )
                    return result

                visited.add(next_id)
                queue.append((next_id, new_factor, new_path))

        return None  # No path found

    def calculate(self, from_uom, to_uom, quantity) -> Decimal:
        """
        Calculate conversion from source to target UoM through chain.

        Args:
            from_uom: Source UnitOfMeasure instance
            to_uom: Target UnitOfMeasure instance
            quantity: Quantity in source unit (Decimal)

        Returns:
            Decimal: Converted quantity in target unit

        Raises:
            ValidationError: If no conversion path exists

        Example:
            result = chain.calculate(mg, ton, Decimal('5000000'))
            # result = Decimal('0.005')
        """
        quantity = Decimal(str(quantity))

        # Same unit
        if from_uom.id == to_uom.id:
            return from_uom.round_quantity(quantity)

        # Find path
        path = self.find_path(from_uom, to_uom)

        if path is None:
            raise ValidationError(
                _('لا يوجد مسار تحويل من %(from)s إلى %(to)s') % {
                    'from': from_uom.name,
                    'to': to_uom.name
                }
            )

        # Calculate conversion using path
        result = quantity
        for i in range(len(path) - 1):
            from_id, to_id = path[i][0], path[i + 1][0]
            factor = self.conversions.get((from_id, to_id), Decimal('1'))
            result = result * factor

        # Round according to target unit precision
        return to_uom.round_quantity(result)

    def get_all_paths(self) -> Dict[Tuple[int, int], List[int]]:
        """
        Get all possible conversion paths in the group.

        Returns:
            Dict mapping (from_id, to_id) to list of intermediate unit IDs

        Useful for:
        - Debugging
        - Visualization
        - Optimization analysis
        """
        from apps.core.models import UnitOfMeasure

        units = UnitOfMeasure.objects.filter(
            company=self.company,
            uom_group=self.group,
            is_active=True
        )

        all_paths = {}

        for from_unit in units:
            for to_unit in units:
                if from_unit.id != to_unit.id:
                    path = self.find_path(from_unit, to_unit)
                    if path:
                        all_paths[(from_unit.id, to_unit.id)] = [
                            uom_id for uom_id, _ in path
                        ]

        return all_paths

    def has_cycle(self) -> bool:
        """
        Check if the conversion graph has a cycle (circular conversion).

        ⭐ NEW Week 2 Day 3

        Uses DFS to detect cycles in the directed graph.

        Returns:
            bool: True if a cycle exists, False otherwise

        Example of cycle:
            A → B (factor 2)
            B → C (factor 3)
            C → A (factor 4)  # Creates a cycle!
        """
        def dfs(node, visited, rec_stack):
            """DFS helper for cycle detection"""
            visited.add(node)
            rec_stack.add(node)

            for neighbor, _ in self.graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor, visited, rec_stack):
                        return True
                elif neighbor in rec_stack:
                    return True  # Cycle detected

            rec_stack.remove(node)
            return False

        visited = set()
        rec_stack = set()

        # Check all nodes
        for node in self.graph.keys():
            if node not in visited:
                if dfs(node, visited, rec_stack):
                    return True

        return False

    def get_conversion_factor(self, from_uom, to_uom) -> Optional[Decimal]:
        """
        Get the total conversion factor from source to target.

        Args:
            from_uom: Source UnitOfMeasure
            to_uom: Target UnitOfMeasure

        Returns:
            Decimal: Total conversion factor, or None if no path

        Example:
            factor = chain.get_conversion_factor(mg, kg)
            # factor = Decimal('0.000001')
            # Meaning: 1 mg = 0.000001 kg
        """
        try:
            result = self.calculate(from_uom, to_uom, Decimal('1'))
            return result
        except ValidationError:
            return None

    def validate_conversion(self, from_uom, to_uom) -> Tuple[bool, str]:
        """
        Validate if conversion is possible between two units.

        Args:
            from_uom: Source UnitOfMeasure
            to_uom: Target UnitOfMeasure

        Returns:
            Tuple[bool, str]: (is_valid, error_message)

        Example:
            valid, error = chain.validate_conversion(kg, liter)
            # (False, "الوحدات من مجموعات مختلفة")
        """
        # Check same group
        if from_uom.uom_group_id != to_uom.uom_group_id:
            return False, _('الوحدات من مجموعات مختلفة')

        # Check path exists
        path = self.find_path(from_uom, to_uom)
        if path is None:
            return False, _('لا يوجد مسار تحويل معرّف')

        return True, ''


def create_conversion_chain(uom_group, company):
    """
    Factory function to create ConversionChain instance.

    Args:
        uom_group: UoMGroup instance
        company: Company instance

    Returns:
        ConversionChain: Initialized chain calculator

    Example:
        chain = create_conversion_chain(weight_group, company)
        result = chain.calculate(mg, kg, 5000)
    """
    return ConversionChain(uom_group, company)


def get_conversion_path_display(from_uom, to_uom, company) -> str:
    """
    Get human-readable conversion path display.

    Args:
        from_uom: Source UnitOfMeasure
        to_uom: Target UnitOfMeasure
        company: Company instance

    Returns:
        str: Path display (e.g., "mg → g → kg → ton")

    Example:
        display = get_conversion_path_display(mg, ton, company)
        # "ميليجرام → جرام → كيلوجرام → طن"
    """
    from apps.core.models import UnitOfMeasure

    if not from_uom.uom_group:
        return f"{from_uom.name} (لا توجد مجموعة)"

    chain = ConversionChain(from_uom.uom_group, company)
    path = chain.find_path(from_uom, to_uom)

    if path is None:
        return _('لا يوجد مسار')

    # Get unit names
    unit_ids = [uom_id for uom_id, _ in path]
    units = UnitOfMeasure.objects.filter(id__in=unit_ids)
    unit_map = {u.id: u.name for u in units}

    names = [unit_map.get(uid, '?') for uid in unit_ids]
    return ' → '.join(names)
