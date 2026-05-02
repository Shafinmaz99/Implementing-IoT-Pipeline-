import heapq
import sqlite3


# 1. WAREHOUSE DATA


warehouse = [
    [0, 0, 1, 0, 0, 0, 0],
    [0, 2, 1, 0, 2, 0, 0],
    [0, 0, 0, 0, 7, 0, 7],
    [0, 1, 0, 1, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 0],
    [0, 2, 7, 0, 0, 0, 7]
]

start_position = (0, 0)

WALKABLE = 0
BLOCKED = 1
NARROW = 2
TARGET = 7

movements = [
    (-1, 0),
    (1, 0),
    (0, -1),
    (0, 1)
]



# 2. DATABASE FUNCTIONS


def get_db_connection():
    connection = sqlite3.connect("warehouse.db")
    connection.row_factory = sqlite3.Row
    return connection


def get_all_products():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()
    connection.close()

    return [
        {
            "id": row["id"],
            "name": row["name"],
            "location": (row["row"], row["col"]),
            "weight": row["weight"]
        }
        for row in rows
    ]


def get_product_by_id(product_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()
    connection.close()

    if row is None:
        return None

    return {
        "id": row["id"],
        "name": row["name"],
        "location": (row["row"], row["col"]),
        "weight": row["weight"]
    }


def get_products_by_ids(product_ids):
    all_products = get_all_products()
    selected = []

    for product_id in product_ids:
        for product in all_products:
            if product["id"] == product_id:
                selected.append(product)
                break

    return selected



# 3. HELPERS


def is_within_bounds(position, warehouse_map):
    row, col = position
    return 0 <= row < len(warehouse_map) and 0 <= col < len(warehouse_map[0])


def is_blocked(position, warehouse_map):
    row, col = position
    return warehouse_map[row][col] == BLOCKED


def is_valid_move(position, warehouse_map):
    return is_within_bounds(position, warehouse_map) and not is_blocked(position, warehouse_map)


def get_cell_value(position, warehouse_map):
    row, col = position
    return warehouse_map[row][col]


def get_valid_neighbors(current_position, warehouse_map):
    row, col = current_position
    neighbors = []

    for move_row, move_col in movements:
        new_position = (row + move_row, col + move_col)
        if is_valid_move(new_position, warehouse_map):
            neighbors.append(new_position)

    return neighbors


def heuristic(current, goal):
    return abs(current[0] - goal[0]) + abs(current[1] - goal[1])


def convert_tuples_to_lists(data):
    if isinstance(data, tuple):
        return list(data)
    elif isinstance(data, list):
        return [convert_tuples_to_lists(item) for item in data]
    elif isinstance(data, dict):
        return {key: convert_tuples_to_lists(value) for key, value in data.items()}
    else:
        return data



# 4. FATIGUE-AWARE COST MODEL


def get_step_cost(position, warehouse_map, carried_weight=0, mode="smart"):
    """
    Base movement cost model.

    basic mode:
        - movement cost
        - narrow path penalty

    smart mode:
        - movement cost
        - stronger narrow-path penalty
        - carried weight penalty
        - fatigue effort penalty grows with carried load
    """
    cell_value = get_cell_value(position, warehouse_map)

    base_cost = 1.0

    if mode == "basic":
        if cell_value == NARROW:
            base_cost += 2.0
        return base_cost

    # SMART MODE
    narrow_penalty = 0.0
    if cell_value == NARROW:
        # make narrow paths more expensive in smart mode
        narrow_penalty = 3.5

    weight_penalty = carried_weight * 0.06
    effort_penalty = carried_weight * 0.025

    total_cost = base_cost + narrow_penalty + weight_penalty + effort_penalty
    return round(total_cost, 4)



# 5. SINGLE ROUTE A*


def find_path_a_star(start, goal, warehouse_map, carried_weight=0, mode="smart"):
    priority_queue = []
    heapq.heappush(priority_queue, (0, 0, start, [start]))
    visited = set()

    while priority_queue:
        f_cost, g_cost, current_position, current_path = heapq.heappop(priority_queue)

        if current_position in visited:
            continue

        visited.add(current_position)

        if current_position == goal:
            return {
                "found": True,
                "target_position": current_position,
                "path": current_path,
                "total_cost": round(g_cost, 2),
                "steps": len(current_path) - 1
            }

        neighbors = get_valid_neighbors(current_position, warehouse_map)

        for neighbor in neighbors:
            if neighbor not in visited:
                step_cost = get_step_cost(neighbor, warehouse_map, carried_weight, mode)
                new_g_cost = g_cost + step_cost
                new_f_cost = new_g_cost + heuristic(neighbor, goal)
                new_path = current_path + [neighbor]

                heapq.heappush(priority_queue, (new_f_cost, new_g_cost, neighbor, new_path))

    return None



# 6. ANALYTICS


def calculate_fatigue_score(steps, narrow_paths, total_weight, mode="smart"):
    if mode == "smart":
        fatigue_score = (steps * 1.0) + (narrow_paths * 2.5) + (total_weight * 0.35)
    else:
        fatigue_score = (steps * 1.0) + (narrow_paths * 2.0)
    return round(fatigue_score, 2)


def classify_fatigue_level(fatigue_score):
    if fatigue_score < 12:
        return "Low"
    elif fatigue_score < 22:
        return "Moderate"
    else:
        return "High"


def analyze_route(path, warehouse_map, total_weight, mode="smart"):
    if path is None:
        return None

    steps = len(path) - 1
    narrow_paths = 0

    for row, col in path:
        if warehouse_map[row][col] == NARROW:
            narrow_paths += 1

    estimated_time_minutes = round(steps * 0.5, 2)
    fatigue_score = calculate_fatigue_score(steps, narrow_paths, total_weight, mode)
    fatigue_level = classify_fatigue_level(fatigue_score)

    efficiency_score = round(max(0, 100 - (fatigue_score * 3.5)), 2)
    safety_score = round(max(0, 100 - (narrow_paths * 12)), 2)

    return {
        "steps": steps,
        "narrow_paths": narrow_paths,
        "estimated_time_minutes": estimated_time_minutes,
        "fatigue_score": fatigue_score,
        "fatigue_level": fatigue_level,
        "total_weight": total_weight,
        "efficiency_score": efficiency_score,
        "safety_score": safety_score
    }


def compare_routes(basic_result, basic_analytics, smart_result, smart_analytics):
    if basic_result is None or smart_result is None:
        return None

    return {
        "basic_cost": basic_result["total_cost"],
        "smart_cost": smart_result["total_cost"],
        "basic_time": basic_analytics["estimated_time_minutes"],
        "smart_time": smart_analytics["estimated_time_minutes"],
        "basic_fatigue": basic_analytics["fatigue_score"],
        "smart_fatigue": smart_analytics["fatigue_score"],
        "cost_difference": round(smart_result["total_cost"] - basic_result["total_cost"], 2),
        "time_difference": round(smart_analytics["estimated_time_minutes"] - basic_analytics["estimated_time_minutes"], 2),
        "fatigue_difference": round(smart_analytics["fatigue_score"] - basic_analytics["fatigue_score"], 2)
    }



# 7. MULTI-ITEM PICKING + RETURN TO BASE


def find_nearest_product(current_position, remaining_products):
    return min(
        remaining_products,
        key=lambda product: heuristic(current_position, product["location"])
    )


def build_multi_pick_route(start, selected_products, warehouse_map, mode="smart"):
    """
    Multi-pick logic:
    start -> pick items -> return to base

    Smart mode:
    - carried weight increases after each pickup
    - return path uses full carried weight
    """
    if not selected_products:
        return None

    remaining_products = selected_products[:]
    current_position = start
    combined_path = [start]
    visit_order = []
    total_cost = 0.0
    carried_weight = 0.0

    # PICKING LEGS
    while remaining_products:
        next_product = find_nearest_product(current_position, remaining_products)

        leg_result = find_path_a_star(
            current_position,
            next_product["location"],
            warehouse_map,
            carried_weight=carried_weight if mode == "smart" else 0,
            mode=mode
        )

        if leg_result is None:
            return None

        leg_path = leg_result["path"]

        if len(leg_path) > 1:
            combined_path.extend(leg_path[1:])

        total_cost += leg_result["total_cost"]

        visit_order.append({
            "id": next_product["id"],
            "name": next_product["name"],
            "location": next_product["location"],
            "weight": next_product["weight"]
        })

        # after pickup, carried weight increases
        carried_weight += next_product["weight"]
        current_position = next_product["location"]
        remaining_products.remove(next_product)

    # RETURN TO BASE
    return_leg = find_path_a_star(
        current_position,
        start,
        warehouse_map,
        carried_weight=carried_weight if mode == "smart" else 0,
        mode=mode
    )

    if return_leg is None:
        return None

    if len(return_leg["path"]) > 1:
        combined_path.extend(return_leg["path"][1:])

    total_cost += return_leg["total_cost"]

    analytics = analyze_route(combined_path, warehouse_map, carried_weight, mode)

    return {
        "mode": mode,
        "selected_products": selected_products,
        "visit_order": visit_order,
        "combined_path": combined_path,
        "return_to_base": True,
        "base_position": start,
        "total_cost": round(total_cost, 2),
        "analytics": analytics
    }



# 8. SINGLE ITEM DASHBOARD DATA


def build_dashboard_data(warehouse_map, start, selected_product, mode="smart"):
    all_products = get_all_products()

    goal = selected_product["location"]
    product_weight = selected_product["weight"]

    basic_result = find_path_a_star(start, goal, warehouse_map, carried_weight=0, mode="basic")
    basic_analytics = analyze_route(basic_result["path"], warehouse_map, 0, mode="basic") if basic_result else None

    smart_result = find_path_a_star(start, goal, warehouse_map, carried_weight=0, mode="smart")
    smart_analytics = analyze_route(smart_result["path"], warehouse_map, product_weight, mode="smart") if smart_result else None

    active_result = basic_result if mode == "basic" else smart_result
    active_analytics = basic_analytics if mode == "basic" else smart_analytics

    dashboard_data = {
        "type": "single",
        "warehouse": {
            "grid": warehouse_map,
            "start_position": start
        },
        "products": all_products,
        "selected_product": selected_product,
        "mode": mode,
        "active_route": {
            "result": active_result,
            "analytics": active_analytics
        },
        "basic_route": {
            "result": basic_result,
            "analytics": basic_analytics
        },
        "smart_route": {
            "result": smart_result,
            "analytics": smart_analytics
        },
        "comparison": compare_routes(basic_result, basic_analytics, smart_result, smart_analytics)
    }

    return convert_tuples_to_lists(dashboard_data)



# 9. MULTI-ITEM DASHBOARD DATA


def build_multi_dashboard_data(warehouse_map, start, selected_products):
    all_products = get_all_products()

    basic_multi = build_multi_pick_route(start, selected_products, warehouse_map, mode="basic")
    smart_multi = build_multi_pick_route(start, selected_products, warehouse_map, mode="smart")

    comparison = None
    if basic_multi and smart_multi:
        comparison = {
            "basic_cost": basic_multi["total_cost"],
            "smart_cost": smart_multi["total_cost"],
            "basic_time": basic_multi["analytics"]["estimated_time_minutes"],
            "smart_time": smart_multi["analytics"]["estimated_time_minutes"],
            "basic_fatigue": basic_multi["analytics"]["fatigue_score"],
            "smart_fatigue": smart_multi["analytics"]["fatigue_score"],
            "cost_difference": round(smart_multi["total_cost"] - basic_multi["total_cost"], 2),
            "time_difference": round(
                smart_multi["analytics"]["estimated_time_minutes"] - basic_multi["analytics"]["estimated_time_minutes"], 2
            ),
            "fatigue_difference": round(
                smart_multi["analytics"]["fatigue_score"] - basic_multi["analytics"]["fatigue_score"], 2
            )
        }

    data = {
        "type": "multi",
        "warehouse": {
            "grid": warehouse_map,
            "start_position": start
        },
        "products": all_products,
        "selected_products": selected_products,
        "basic_multi_route": basic_multi,
        "smart_multi_route": smart_multi,
        "comparison": comparison
    }

    return convert_tuples_to_lists(data)