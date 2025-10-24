import type_enforced
from fizgrid.utils import unique_id, ShapeMoverUtils, Shape


@type_enforced.Enforcer(enabled=True)
class Entity:
    def __init__(
        self,
        name: str,
        shape: list[list[int | float]],
        x_coord: int | float,
        y_coord: int | float,
        auto_rotate: bool = False,
        location_precision: int = 4,
    ):
        """
        Initializes an entity with a given shape and location in the grid.

        Args:

        - id (int): The ID of the entity.
        - name (str): The name of the entity.
        - shape (list[list[int|float]]): The shape of the entity as a list of points centered around the shape origin.
            - The shape origin referenced here should be the center of the shape as the shape origin is used to determine how the shape is located on the grid.
            - The shape is a list of points, where each point is a list of two coordinates [x, y] relative to the shape origin.
        - x_coord (int|float): The starting x-coordinate of the entity in the grid.
        - y_coord (int|float): The starting y-coordinate of the entity in the grid.
        - auto_rotate (bool): Whether to automatically rotate the shape based on the direction of movement.
            - Note: The default assumption is that the shape is facing right (0 radians).
        - location_precision (int): The precision of the location coordinates. This is used to round the coordinates to a specific number of decimal places.
        """
        self.id = unique_id()
        """The ID of the entity."""
        self.name = name
        """The name of the entity."""
        self.shape = shape
        """The shape of the entity as a list of points centered around the shape the current (x, y) coordinates."""
        self.x_coord = x_coord
        """
        The x-coordinate of the entity in the grid. This is the last known location of the entity.
        
        - Note: This is only updated when events realize the route. This means that a route in progress would not have the correct
            location until the route is realized (either completed or interrupted by a cancellation or collision).
        """
        self.y_coord = y_coord
        """
        The y-coordinate of the entity in the grid. This is the last known location of the entity.
        
        - Note: This is only updated when events realize the route. This means that a route in progress would not have the correct
            location until the route is realized (either completed or interrupted by a cancellation or collision).
        """
        self.history = []
        """
        The history of the entity's location and collision status. 
        This is a list of dictionaries containing the x, y, t, and c values.

        - x (int|float): The x-coordinate of the entity in the grid.
        - y (int|float): The y-coordinate of the entity in the grid.
        - t (int|float): The time at which the entity was at this location.
        - c (bool): Whether the entity was in a collision at this time.

        - Note: This is only updated when events realize the route. This means that a route in progress would not have history until the
            route is realized (either completed or interrupted by a cancellation or collision).
        """

        # Util Attributes
        self.__grid__ = None
        self.__on_grid__ = False
        self.__route_start_time__ = None
        self.__blocked_grid_cells__ = []
        self.__planned_waypoints__ = []
        self.__future_event_ids__ = {"system": {}, "user": {}}
        self.__shape_current__ = shape
        self.__auto_rotate__ = auto_rotate
        self.__location_precision__ = location_precision
        self.__is_available__ = True

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name})"

    def __assoc_grid__(self, grid) -> None:
        """
        Associate the grid to this entity.
        Creates a reference in both the grid and the entity to allow easy access from both directions.

        Args:

        - grid (Grid): The grid to assign to this entity.
        """
        if self.__grid__ is not None:
            raise Exception(
                f"Entity {self.name} is already associated with a grid. Cannot associate with a new grid."
            )
        self.__grid__ = grid

    def __place_on_grid__(
        self,
        safe_create: bool = False,
        safe_create_increment: int = 5,
        safe_create_attempts: int = 10,
        safe_create_on_error: str = "raise_exception",
        safe_create_attempt: int = 0,
    ) -> None:
        """
        Place this entity on the grid and claim the grid cells it will block.

        This allows the entity to take up space and move around the grid.

        Args:

        - safe_create: A boolean indicating whether to attempt safe creation of the obstruction.
            - If True, the method will attempt to create the obstruction without overlapping existing obstructions.
            - If False, it may raise an error if there is an overlap between obstructions / other entities.
            - Default is False.
        - safe_create_increment: The incremental time to wait to use when attempting safe creation if an overlap is detected.
            - Default is 5 time units.
        - safe_create_attempts: The maximum number of attempts to try creating the obstruction safely before logging an error.
            - Default is 10 attempts.
        - safe_create_on_error: The action to take if safe creation fails after the maximum attempts.
            - Options are "print_error" to log an error message, or "raise_exception" to raise an exception.
            - Default is "print_error".
        - safe_create_attempt: The current attempt number for safe creation.
            - Default is 0.
        """
        if self.__grid__ is None:
            raise Exception(
                f"Entity {self.name} is not associated with a grid. Cannot place on grid."
            )
        if self.__on_grid__:
            raise Exception(
                f"Entity {self.name} is already on the grid. Cannot place on grid again."
            )

        if safe_create:
            current_time = self.get_time()
            blocks = ShapeMoverUtils.moving_shape_overlap_intervals(
                x_coord=self.x_coord,
                y_coord=self.y_coord,
                x_shift=0,
                y_shift=0,
                t_start=current_time,
                t_end=current_time + 1,
                shape=self.__shape_current__,
                cell_density=self.__grid__.__cell_density__,
            )
            has_collision = False
            for (x_cell, y_cell), (t_start, t_end) in blocks.items():
                cell = self.__grid__.__cells__[y_cell][x_cell]
                # Check for collisions with other entities in the cell
                for (
                    other_t_start,
                    other_t_end,
                    other_entity_id,
                ) in cell.values():
                    # Note: This does not use t_start and t_end as we only check for the current point in time,
                    # but ShapeMoverUtils requires a non zero time interval to calculate the blocks
                    if (
                        current_time < other_t_end
                        and current_time >= other_t_start
                    ):
                        has_collision = True
                        break
                if has_collision:
                    break
            if has_collision:
                if safe_create_attempt >= safe_create_attempts:
                    if safe_create_on_error == "raise_exception":
                        raise Exception(
                            f"Entity {self.name} could not be placed on the grid without overlapping other entities after {safe_create_attempts} attempts."
                        )
                    elif safe_create_on_error == "print_error":
                        print(
                            f"Warning: Entity {self.name} could not be placed on the grid without overlapping other entities after {safe_create_attempts} attempts."
                        )
                        return
                else:
                    # Try again after incrementing the time
                    self.__grid__.add_event(
                        time=current_time + safe_create_increment,
                        object=self,
                        method="__place_on_grid__",
                        kwargs={
                            "safe_create": True,
                            "safe_create_increment": safe_create_increment,
                            "safe_create_attempts": safe_create_attempts,
                            "safe_create_on_error": safe_create_on_error,
                            "safe_create_attempt": safe_create_attempt + 1,
                        },
                        priority=5,
                    )
                    return

        self.__on_grid__ = True
        self.__route_start_time__ = self.get_time()
        self.history.append(
            {
                "x": self.x_coord,
                "y": self.y_coord,
                "t": self.get_time(),
                "c": False,
            }
        )
        self.__realize_route__(
            is_result_of_collision=False,
            raise_on_future_collision=True,
            is_result_of_dissoc_grid=False,
            clear_event_types=["system"],
        )

    def __dissoc_grid__(self) -> None:
        """
        Dissociate the grid from this entity.
        This method removes the entity from the grid and clears any blocked grid cells and future events.
        """
        if self.__grid__ is None:
            raise Exception(
                f"Entity {self.name} is not associated with a grid. Cannot dissociate from grid."
            )
        if self.__on_grid__:
            self.__realize_route__(
                is_result_of_collision=False,
                raise_on_future_collision=False,
                is_result_of_dissoc_grid=True,
            )
        # Clear the blocked grid cells and future events
        self.__clear_blocked_grid_cells__()
        self.__clear_future_events__(clear_event_types=["system", "user"])
        self.__route_start_time__ = None
        self.__grid__ = None
        self.__on_grid__ = False

    def __clear_blocked_grid_cells__(self) -> None:
        """
        Clears the blocked grid cells for this entity.
        """
        for x_cell, y_cell, block_id in self.__blocked_grid_cells__:
            cell = self.__grid__.__cells__[y_cell][x_cell]
            cell.pop(block_id, None)
        self.__blocked_grid_cells__ = []

    def __clear_future_events__(self, clear_event_types=["system"]) -> None:
        """
        Clears the future events for this entity.
        """
        for event_type in clear_event_types:
            for (
                this_event_id,
                related_event_id,
            ) in self.__future_event_ids__[event_type].items():
                # Remove the event from the queue
                event_obj = self.__grid__.__queue__.remove_event(this_event_id)
                # If this event is a standard route_end event, it will not have an related event, so we can be done here
                # If the event_obj is None, it has already been processed or removed so we can skip any further processing
                # If this event is a collision event, it will have an associated event and should be removed too
                if related_event_id != None and event_obj != None:
                    self.__grid__.__queue__.remove_event(related_event_id)
            self.__future_event_ids__[event_type] = {}

    def __waypoint_check__(self, waypoints) -> None:
        """
        Checks the waypoints for validity.
        Raises an exception if the waypoints are not valid.

        Args:

        - waypoints (list[tuple[int|float,int|float,int|float]]): A list of waypoints to be added to the grid queue.
        """
        for waypoint in waypoints:
            if len(waypoint) != 3:
                raise Exception(
                    f"Waypoint must be a tuple of (x_coord, y_coord, time_shift). Waypoint: {waypoint}"
                )
            if waypoint[0] < 0 or waypoint[1] < 0 or waypoint[2] < 0:
                raise Exception(
                    f"Waypoint coordinates and times must be positive. Waypoint: {waypoint}"
                )
            if (
                waypoint[0] > self.__grid__.__x_size__
                or waypoint[1] > self.__grid__.__y_size__
            ):
                raise Exception(
                    f"Waypoint coordinates must be within the grid. Waypoint: {waypoint}"
                )

    def __plan_route__(
        self,
        waypoints: list[tuple[int | float, ...]],
        raise_on_future_collision: bool = False,
        bypass_availability_check: bool = False,
        return_collisions: bool = False,
    ) -> dict:
        """
        Sets the route for this entity given a set of waypoints starting at the current time.
        Determines the cells this entity will block and at which times it will block them.
        Checks for collisions with other entities.
        Adds events to the queue for the first collision with each colliding entity.
          - Note: Not all events will occur, and future events will be cleared when the first event occurs.

        Args:

        - waypoints (list[tuple[int|float,int|float,int|float]]): A list of waypoints to be added to the grid queue.
            - A list of tuples where each tuple is (x_coord, y_coord, time_shift).
            - EG:
                ```
                waypoints = [
                    (5, 3, 10),
                    (3, 5, 10)
                ]
                ```
                - Move to (5, 3) over 10 seconds
                - Move to (3, 5) over 10 seconds
            - Note: x_coord and y_coord are the coordinates of the waypoint. They must both be positive.
            - Note: time_shift is the time it takes to move to the waypoint. It must be positive.
            - Optionally, you can use a 4th element to specify the orientation of the shape.
                - This orientation is always relative to the original shape
                - This is in radians where 0 is facing right (equivalent to the initial shape orientation) and pi is facing left.
                - Note: The last used orientation is used until it is changed again (or auto_rotate is set to True).
            - Note: x_coord and y_coord are the coordinates of the waypoint. They must both be positive.
            - Note: time_shift is the time it takes to move to the waypoint. It must be positive.
        - raise_on_future_collision (bool): Whether to raise an exception if the entity has any future plans that result in a collision.
            - Note: This will raise an exception even if the future collision would not happen due to another event occurring first.
            - Note: This is mostly used when initially placing entities on the grid to ensure they are not placed in a collision.
        - bypass_availability_check (bool): Whether to bypass the availability check for this entity.
            - Note: This is used when adding a route to the queue without checking if the entity is available.
        - return_collisions (bool): Whether to return the collisions dictionary when finished planning the route.

        Returns:

        - dict: A dictionary containing the following keys:
            - has_collision (bool): Whether the route has a collision with another entity.
            - collisions (dict): A dictionary of colliding entity ids (keys) and their collision times (values).
                - Only returned if return_collisions is True.
        """
        if not self.__on_grid__:
            raise Exception(
                "Entity is not on this grid yet, but is attempting to plan a route. Either it has not been assigned to this grid, or the time it will be placed on the grid is in the future."
            )
        # Raise an exception if the entity is already in a route
        if not self.__is_available__:
            if not bypass_availability_check:
                raise Exception(
                    f"Entity {self.name} is not available for a new route. Cannot set a new route until the current route is finished."
                )

        # Check for valid waypoints
        self.__waypoint_check__(waypoints)
        waypoints = list(
            waypoints
        )  # Make a copy of the waypoints to avoid modifying the original list

        # Setup util attributes
        self.__clear_blocked_grid_cells__()
        self.__clear_future_events__(clear_event_types=["system"])

        x_tmp = self.x_coord
        y_tmp = self.y_coord
        t_tmp = self.get_time()

        collisions = {}
        total_route_time_shift = sum([waypoint[2] for waypoint in waypoints])

        if total_route_time_shift > 0:
            self.__is_available__ = False

        # Add a final waypoint occuring until the end of the simulation.
        # This allows us to lock in the position of the entity at the end of the route and block the grid cells accordingly.
        if len(waypoints) > 0:
            waypoints.append(
                (
                    waypoints[-1][0],
                    waypoints[-1][1],
                    max(
                        self.__grid__.__max_time__
                        - t_tmp
                        - total_route_time_shift,
                        0,
                    ),
                )
            )
        else:
            waypoints.append(
                (
                    self.x_coord,
                    self.y_coord,
                    max(
                        self.__grid__.__max_time__
                        - t_tmp
                        - total_route_time_shift,
                        0,
                    ),
                )
            )

        # Store the route waypoints and start time for later use to determine the entity's position at a given time
        self.__planned_waypoints__ = waypoints
        self.__route_start_time__ = self.get_time()
        route_end_time = min(
            self.__grid__.__max_time__,
            self.__route_start_time__ + total_route_time_shift,
        )

        # For each route waypoint, calculate the blocks and collisions and add them to the grid
        for waypoint in waypoints:
            x_shift = waypoint[0] - x_tmp
            y_shift = waypoint[1] - y_tmp
            if len(waypoint) == 4:
                orientation = waypoint[3]
                self.__shape_current__ = Shape.rotate(
                    radians=orientation, shape=self.shape
                )
            elif self.__auto_rotate__:
                if x_shift != 0 or y_shift != 0:
                    self.__shape_current__ = Shape.get_rotated_shape(
                        shape=self.shape, x_shift=x_shift, y_shift=y_shift
                    )
            blocks = ShapeMoverUtils.moving_shape_overlap_intervals(
                x_coord=x_tmp,
                y_coord=y_tmp,
                x_shift=x_shift,
                y_shift=y_shift,
                t_start=t_tmp,
                t_end=t_tmp + waypoint[2],
                shape=self.__shape_current__,
                cell_density=self.__grid__.__cell_density__,
            )
            x_tmp = waypoint[0]
            y_tmp = waypoint[1]
            t_tmp = t_tmp + waypoint[2]
            for (x_cell, y_cell), (t_start, t_end) in blocks.items():
                # Check if the cell is within the grid bounds
                if (
                    x_cell < 0
                    or y_cell < 0
                    or x_cell
                    >= self.__grid__.__x_size__ * self.__grid__.__cell_density__
                    or y_cell
                    >= self.__grid__.__y_size__ * self.__grid__.__cell_density__
                ):
                    # Note: Shape coords outside of the grid raise an exception, but this this would indicate that the shape may have an overlap over the edge.
                    # Note: If there are exterior walls, no exception here should be necessary
                    # TODO: Determine if this should be an exception or just a warning
                    # print(f"Warning: Entity {self.name} is outside of the grid bounds is outside of the grid bounds based on its shape.")
                    continue
                # Store a unique block_id to allow for removal of the block later
                block_id = unique_id()
                # Get the relevant cell in the grid
                cell = self.__grid__.__cells__[y_cell][x_cell]
                # Check for collisions with other entities in the cell
                for (
                    other_t_start,
                    other_t_end,
                    other_entity_id,
                ) in cell.values():
                    if t_start < other_t_end and t_end > other_t_start:
                        # Determine the time of the collision and store the most recent collision time with each colliding entity
                        collision_time = max(t_start, other_t_start)
                        previous_collision_time = collisions.get(
                            other_entity_id
                        )
                        if (
                            previous_collision_time is None
                            or collision_time < previous_collision_time
                        ):
                            collisions[other_entity_id] = collision_time
                # Block the grid cell for the entity
                cell[block_id] = (t_start, t_end, self.id)
                # Store the blocked grid cell for later removal
                self.__blocked_grid_cells__.append((x_cell, y_cell, block_id))
        if raise_on_future_collision and len(collisions) > 0:
            raise Exception(
                f"{self.__repr__()} collides with other entities now or in the future. "
            )
        # Create collision events for the first collision with each colliding entity
        for other_entity_id, collision_time in collisions.items():
            other_entity = self.__grid__.__entities__[other_entity_id]
            event_id = self.__grid__.add_event(
                time=collision_time,
                object=self,
                method="__realize_route__",
                kwargs={
                    "is_result_of_collision": True,
                    "clear_event_types": ["system", "user"],
                },
                priority=3,
            )
            other_event_id = self.__grid__.add_event(
                time=collision_time,
                object=other_entity,
                method="__realize_route__",
                kwargs={
                    "is_result_of_collision": True,
                    "clear_event_types": ["system", "user"],
                },
                priority=3,
            )
            # Store the event_id for each entity involved in the collision
            self.__future_event_ids__["system"][event_id] = other_event_id
            other_entity.__future_event_ids__["system"][
                other_event_id
            ] = event_id

        if route_end_time > self.get_time():
            # Add a route_end event for this entity at the timing of the end of the route
            event_id = self.__grid__.add_event(
                time=route_end_time,
                object=self,
                method="__realize_route__",
                kwargs={
                    "is_result_of_collision": False,
                    "clear_event_types": ["system"],
                },
                priority=2,
            )
            self.__future_event_ids__["system"][event_id] = None
        output = {
            "has_collision": len(collisions) > 0,
        }
        if return_collisions:
            output["collisions"] = collisions
        return output

    def __realize_route__(
        self,
        is_result_of_collision: bool = False,
        raise_on_future_collision: bool = False,
        is_result_of_dissoc_grid: bool = False,
        clear_event_types: list[str] = ["system"],
    ) -> dict:
        """
        Realize the route for this entity at the current time.

        Args:

        - is_result_of_collision (bool): Whether this route end is the result of a collision.
        - raise_on_future_collision (bool): Whether to raise an exception if the entity is in a future collision.
            - Raises an exception if this event causes a future collision with another entity.
        - is_result_of_dissoc_grid (bool): Whether the entity will be removed from the grid after this event.
        -clear_event_types (list[str]): A list of event types to clear when realizing the route.
            - Note: This is used to clear the future events for this entity when realizing a new route.

        Returns:

        - dict: A dictionary containing the following keys:
            - has_collision (bool): Whether the route has a collision with another entity.
        """
        # Set this entity as available for a new route
        self.__is_available__ = True
        # Determeine Realized Route and update the entity's position / history
        x_coord, y_coord = self.get_current_location(update_history=True)
        # If the entity is in a collision, update the last history entry to reflect that
        if is_result_of_collision:
            self.history[-1]["c"] = True

        # Set the entity's position to where they are at this point in time
        self.x_coord = x_coord
        self.y_coord = y_coord

        if is_result_of_dissoc_grid:
            return {"is_result_of_collision": False}
        # Stop the entity at their current location and update the grid for their expected future
        self.__clear_future_events__(clear_event_types=clear_event_types)
        planned_route = self.__plan_route__(
            waypoints=[], raise_on_future_collision=raise_on_future_collision
        )
        self.on_realize(is_result_of_collision=is_result_of_collision)
        return planned_route

    def get_time(self) -> int | float:
        """
        Returns the current time of the grid queue.
        This method retrieves the current time from the grid queue.

        Returns:

        - int|float: The current time of the grid queue.
        """
        return self.__grid__.__queue__.__time__

    def check_route(
        self,
        waypoints: list[tuple[int | float, int | float, int | float]],
    ):
        """
        Checks the route for this entity at the current simulation time without actually planning the route.
        This method is used to check if the route is valid and does not cause any collisions with other entities.
        - Note: The entity must be available for this check to work and this does not change the entity's availability.
        - Note: This does not update the entity's position or history.

        Args:

        - waypoints (list[tuple[int | float, int | float, int | float]]): A list of waypoints to check.

        Returns:
        - dict: A dictionary containing the following keys:
            - has_collision (bool): Whether the route has a collision with another entity.
            - collisions (dict): A dictionary of colliding entity ids (keys) and their collision times (values).

        """
        if not self.__is_available__:
            raise Exception("Only available entities can check routes.")
        output = self.__plan_route__(
            waypoints=waypoints,
            return_collisions=True,
        )
        self.__clear_future_events__(clear_event_types=["system", "user"])
        self.__is_available__ = True
        self.__plan_route__(
            waypoints=[],
        )
        return output

    def add_route(
        self,
        waypoints: list[tuple[int | float, int | float, int | float]],
        time: int | float | None = None,
    ) -> None:
        """
        Adds a route to the grid for this entity. Mutliple routes can be added for future planning.
        - Note, collisions and route cancel events will cause future routes to be cleared.

        Args:

        - waypoints (list[tuple[int|float,int|float,int|float]]): A list of waypoints to be added to the grid queue.
            - A list of tuples where each tuple is (x_coord, y_coord, time_shift).
            - EG:
                ```
                waypoints = [
                    (5, 3, 10),
                    (3, 5, 10)
                ]
                ```
                - Move to (5, 3) over 10 seconds
                - Move to (3, 5) over 10 seconds
            - Note: x_coord and y_coord are the coordinates of the waypoint. They must both be positive.
            - Note: time_shift is the time it takes to move to the waypoint. It must be positive.
            - Optionally, you can use a 4th element to specify the orientation of the shape.
                - This orientation is always relative to the original shape
                - This is in radians where 0 is facing right (equivalent to the initial shape orientation) and pi is facing left.
                - Note: The last used orientation is used until it is changed again (or auto_rotate is set to True).
        - time (int|float|None): The time at which to start the route. If None, the current time is used.
        """
        if self.__grid__ is None:
            raise Exception(
                "Entity is not assigned to a grid. Cannot add a route."
            )
        if time is None:
            time = self.get_time()
        # Add the event to the queue
        event_id = self.__grid__.add_event(
            time=time,
            object=self,
            method="__plan_route__",
            kwargs={
                "waypoints": waypoints,
            },
            priority=0,
        )
        self.__future_event_ids__["user"][event_id] = None

    def get_current_location(
        self, update_history: bool = False
    ) -> tuple[int | float, int | float]:
        """
        Returns the current location of the entity as a tuple of (x_coord, y_coord).

        This method retrieves the current coordinates of the entity from its attributes.

        Args:

        - update_history (bool): Whether to update the history with the current location.
            - Note: This is used for internal purposes to update the history when the entity is moved or when the route is realized.

        Returns:

        - tuple[int | float, int | float]: The current coordinates of the entity.
        """
        x_loc = self.x_coord
        y_loc = self.y_coord
        t_loc = self.__route_start_time__
        current_time = self.get_time()
        # Add the initial location to the history to signify when the route started
        if (
            update_history
            and len(self.__planned_waypoints__) > 0
            and current_time >= t_loc
        ):
            self.history.append(
                {
                    "x": x_loc,
                    "y": y_loc,
                    "t": t_loc,
                    "c": False,
                }
            )
        for waypoint in self.__planned_waypoints__:
            # End the route realization if the time is greater than the current time
            if t_loc >= current_time:
                break
            # Get partial location if interrupted by the current time
            elif t_loc + waypoint[2] > current_time:
                pct_complete = (current_time - t_loc) / waypoint[2]
                x_loc = (waypoint[0] - x_loc) * pct_complete + x_loc
                y_loc = (waypoint[1] - y_loc) * pct_complete + y_loc
                t_loc = current_time
            # Otherwise, update the tmp location
            else:
                x_loc = waypoint[0]
                y_loc = waypoint[1]
                t_loc = t_loc + waypoint[2]

            # This rounding is needed to ensure that rounding errors in python do not create a permanent collisions between entities
            x_loc = round(x_loc, self.__location_precision__)
            y_loc = round(y_loc, self.__location_precision__)
            if update_history:
                # Update the history with the current location
                # Note: This is only done if update_history is True, which is used to update the history when the entity is moved
                #       or when the route is realized.
                self.history.append(
                    {
                        "x": x_loc,
                        "y": y_loc,
                        "t": t_loc,
                        "c": False,  # This is updated to True in the realize_route method if the entity is in a collision
                    }
                )

        return (x_loc, y_loc)

    def cancel_route(
        self,
        time: int | float | None = None,
    ) -> None:
        """
        Cancels the route and all future plans for this entity.

        The entity is stopped at its current location and is available for a new route.

        Args:

        - time (int|float|None): The time at which to cancel the route. If None, the current time is used.
        """
        if self.__grid__ is None:
            raise Exception(
                "Entity is not assigned to a grid. Cannot cancel a route."
            )
        if time is None:
            time = self.get_time()
        # Add the event to the queue
        event_id = self.__grid__.add_event(
            time=time,
            object=self,
            method="__realize_route__",
            kwargs={
                "clear_event_types": ["system", "user"],
            },
            priority=4,
        )
        self.__future_event_ids__["user"][event_id] = None

    def on_realize(self, **kwargs):
        """
        Called when the route is realized to allow for custom behavior.
        This method should be overridden by subclasses to implement custom behavior.

        Args:

        - **kwargs: Additional arguments passed to the method. Subclasses may use this or add their own arguments.
        """


class StaticEntity(Entity):
    """
    This class is used to represent entities that do not move, such as walls or other static objects.

    This is an extension of the Entity class that represents a static entity.

    To improve efficiency, many events and logic are avoided as a static entity does not move or respond to events.
    """

    def __realize_route__(
        self,
        is_result_of_collision: bool = False,
        raise_on_future_collision: bool = False,
        is_result_of_dissoc_grid: bool = False,
        clear_event_types: list[str] = ["system"],
    ) -> dict:
        """
        Realize the route for this entity at the current time.

        Args:

        - is_result_of_collision (bool): Whether this route end is the result of a collision.
            - If True, the route end is the result of a collision and the entity should not be allowed to start a new route until the collision is resolved.
            - If False, the route end is not the result of a collision and the entity should be allowed to start a new route.
        - raise_on_future_collision (bool): Whether to raise an exception if the entity is in a future collision.
            - Raises an exception if this event causes a future collision with another entity.
        - is_result_of_dissoc_grid (bool): Whether the entity will be removed from the grid after this event.

        Returns:

        - dict: A dictionary containing the following keys:
            - has_collision (bool): Whether the route has a collision with another entity.
        """
        self.__is_available__ = True
        # Since this is a static entity, we don't need to do anything here.
        if is_result_of_collision:
            return
        if is_result_of_dissoc_grid:
            super().__realize_route__(
                is_result_of_collision=False,
                raise_on_future_collision=False,
                is_result_of_dissoc_grid=True,
                clear_event_types=["system", "user"],
            )
        # Since this object does not move, we don't need to plan a route and will never interrupt it.
        return self.__plan_route__(
            waypoints=[], raise_on_future_collision=raise_on_future_collision
        )

    def add_route(self, *arts, **kwargs) -> None:
        """
        Static entities cannot have routes. They are static and do not move. This method raises an exception if called.
        """
        raise Exception(
            "Static entities cannot have routes. They are static and do not move."
        )

    def cancel_route(self, *args, **kwargs) -> None:
        """
        Static entities cannot have routes. They are static and do not move. This method raises an exception if called.
        """
        raise Exception(
            "Static entities cannot have routes. They are static and do not move."
        )


class GhostEntity(Entity):
    """
    This class is used to represent entities that do not collide with other entities.

    It is an extension of the Entity class that represents a ghost entity.

    Essentially, these entities can move freely without worrying about collisions. Using them avoids substantial overhead in the simulation and can dramatically improve performance if collisions are irrelevant.
    """

    def __plan_route__(
        self,
        waypoints: list[tuple[int | float, int | float, int | float]],
        raise_on_future_collision: bool = False,
        bypass_availability_check: bool = False,
    ) -> dict:
        """
        Overrides the __plan_route__ method to allow for a ghost entity to be placed on the grid that never collides with other entities because it does not check for collisions.

        Sets the route for this entity given a set of waypoints starting at the current time.

        Args:

        - waypoints (list[tuple[int|float,int|float,int|float]]): A list of waypoints to be added to the grid queue.
            - A list of tuples where each tuple is (x_coord, y_coord, time_shift).
            - EG:
                ```
                waypoints = [
                    (5, 3, 10),
                    (3, 5, 10)
                ]
                ```
                - Move to (5, 3) over 10 seconds
                - Move to (3, 5) over 10 seconds
            - Note: x_coord and y_coord are the coordinates of the waypoint. They must both be positive.
            - Note: time_shift is the time it takes to move to the waypoint. It must be positive.
            - Optionally, you can use a 4th element to specify the orientation of the shape.
                - This orientation is always relative to the original shape
                - This is in radians where 0 is facing right (equivalent to the initial shape orientation) and pi is facing left.
                - Note: The last used orientation is used until it is changed again (or auto_rotate is set to True).
        - raise_on_future_collision (bool): Whether to raise an exception if the entity has any future plans that result in a collision.
            - Note: This is not used for ghost entities, but is included for consistency with the parent class.
        - bypass_availability_check (bool): Whether to bypass the availability check for this entity.
            - Note: This is used when adding a route to the queue without checking if the entity is available.


        Returns:

        - dict: A dictionary containing the following keys:
            - has_collision (bool): Whether the route has a collision with another entity.
                - Note: This will always be False for ghost entities.
        """
        # Raise an exception if the entity is already in a route
        if not self.__is_available__:
            if not bypass_availability_check:
                raise Exception(
                    f"entity {self.name} is not available for a new route. Cannot set a new route until the current route is finished."
                )

        # Check for valid waypoints
        self.__waypoint_check__(waypoints)

        # Setup util attributes
        self.__clear_future_events__(clear_event_types=["system"])

        total_route_time_shift = sum([waypoint[2] for waypoint in waypoints])

        self.__route_start_time__ = self.get_time()

        # Add a final waypoint occuring until the end of the simulation.
        # This allows us to lock in the position of the entity at the end of the route and block the grid cells accordingly.
        if len(waypoints) > 0:
            waypoints.append(
                (
                    waypoints[-1][0],
                    waypoints[-1][1],
                    self.__grid__.__max_time__
                    - self.__route_start_time__
                    - total_route_time_shift,
                )
            )
        else:
            waypoints.append(
                (
                    self.x_coord,
                    self.y_coord,
                    self.__grid__.__max_time__
                    - self.__route_start_time__
                    - total_route_time_shift,
                )
            )

        # Store the route waypoints and start time for later use to determine the entity's position at a given time
        self.__planned_waypoints__ = waypoints
        route_end_time = min(
            self.__grid__.__max_time__,
            self.__route_start_time__ + total_route_time_shift,
        )

        if route_end_time > self.get_time():
            # Add a route_end event for this entity at the timing of the end of the route
            event_id = self.__grid__.add_event(
                time=route_end_time,
                object=self,
                method="__realize_route__",
                kwargs={
                    "is_result_of_collision": False,
                },
                priority=2,
            )
            self.__future_event_ids__["system"][event_id] = None
        return {"has_collision": False}
