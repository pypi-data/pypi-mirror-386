import type_enforced
from fizgrid.entities import Entity, StaticEntity
from fizgrid.queue import TimeQueue


@type_enforced.Enforcer(enabled=True)
class Grid:
    def __init__(
        self,
        name: str,
        x_size: int,
        y_size: int,
        max_time: int = 1000,
        add_exterior_walls: bool = True,
        cell_density: int = 1,
    ):
        """
        Initializes a grid with the specified parameters.

        Args:

        - name (str): The name of the grid.
        - x_size (int): The width of the grid.
        - y_size (int): The height of the grid.
        - max_time (int): The maximum time for the grid simulation.
        - add_exterior_walls (bool): Whether to add exterior walls to the grid.
            - Default: True
        - cell_density (int): The number of cells per unit of length.
            - Default: 1
        """
        assert cell_density > 0, "cell_density must be greater than 0"
        # Passed Attributes
        self.name: str = name
        """The name of the grid."""
        self.__x_size__ = x_size
        self.__y_size__ = y_size
        self.__max_time__ = max_time
        self.__cell_density__ = cell_density

        # Calculated Attributes
        self.__entities__ = {}
        self.__queue__ = TimeQueue()
        self.__cells__ = [
            [{} for _ in range(x_size * cell_density)]
            for _ in range(y_size * cell_density)
        ]

        if add_exterior_walls:
            self.add_exterior_walls()

    def __repr__(self):
        return f"Grid({self.name} {self.__x_size__}x{self.__y_size__})"

    def add_entity(
        self,
        entity: Entity,
        time: int | float | None = None,
        safe_create: bool = False,
        safe_create_increment: int = 5,
        safe_create_attempts: int = 10,
        safe_create_on_error: str = "raise_exception",
    ):
        """
        Adds an entity to the grid.

        Args:

        - entity (Entity): The entity to be added to the grid.
            - Must be an Entity or a subclass of Entity.
        - time (int|float|None): The time at which the entity should be added to the grid.
            - If None, the entity is added immediately.
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
            - Default is "raise_exception".

        Returns:

        - Entity: The added entity.
        """
        entity.__assoc_grid__(self)
        self.__entities__[entity.id] = entity
        kwargs = {
            "safe_create": safe_create,
            "safe_create_increment": safe_create_increment,
            "safe_create_attempts": safe_create_attempts,
            "safe_create_on_error": safe_create_on_error,
        }
        if time is None:
            entity.__place_on_grid__(**kwargs)
        else:
            self.add_event(
                time=time,
                object=entity,
                method="__place_on_grid__",
                kwargs=kwargs,
                priority=5,
            )
        return entity

    def remove_entity(self, entity: Entity, time: int | float | None = None):
        """
        Removes an entity from the grid.

        Args:

        - entity (Entity): The entity to be removed from the grid.
            - Must be an Entity or a subclass of Entity.
        - time (int|float|None): The time at which the entity should be removed from the grid.
            - If None, the entity is removed immediately.
        """
        if time is not None:
            self.add_event(
                time=time,
                object=self,
                method="remove_entity",
                kwargs={"entity": entity},
                priority=1,
            )
            return entity
        if entity.id in self.__entities__:
            entity.__dissoc_grid__()
            self.__entities__.pop(entity.id, None)

    def add_event(
        self,
        time: int | float,
        object,
        method: str,
        kwargs: dict = dict(),
        priority: int = 0,
    ) -> int:
        """
        Adds an event to the queue.
        This method schedules an event for a specific object at a specific time.
        Essentially, it allows you to schedule a method call on an object at a specific time.

        Args:

        - time (int|float): The time at which the event should occur.
        - object: The object on which the event will occur.
        - method (str): The name of the method to be called on the object.
        - kwargs (dict): The keyword arguments to be passed to the method.
        - priority (int): The priority of the event.
            - Default: 0
            - Higher values indicate higher priority.
            - This is used to determine the order of events with the same time.
            - If two events have the same time, the one with the higher priority will be processed first.
            - If the priority is the same, the event with the lower ID will be processed first.
            - In general:
                - Adding an entity to the grid: 5
                - Canceling a route: 4
                - Handling collisions: 3
                - Resolving an end of route: 2
                - Removing an entity from the grid: 1
                - Adding a Route: 0
                - Adding an event: 0

        Returns:

        - int: The ID of the added event as generated by the queue.
        """
        return self.__queue__.add_event(
            time=time,
            event={"object": object, "method": method, "kwargs": kwargs},
            priority=priority,
        )

    def get_time(self) -> int | float:
        """
        Returns the current time of the grid.
        This method retrieves the current time from the queue.

        Returns:

        - int|float: The current time of the grid.
        """
        return self.__queue__.__time__

    def resolve_next_state(self) -> list[dict]:
        """
        Resolves the next state of the grid.
        This method processes the next event in the queue and updates the grid accordingly.

        Returns:

        - list[dict]: A list of events that were processed in this step.
            - Each event is a dictionary containing a time, id and event.
            - The event dictionary contains the object, method and kwargs.
                - id (int): The ID of the event as generated by the queue.
                - time (int|float): The time at which the event occurred.
                - event (dict): The event that was processed.
                    - object: The object on which the event occurred.
                    - method (str): The name of the method that was called.
                    - kwargs (dict): The keyword arguments that were passed to the method.
        """
        event_items = self.__queue__.get_next_events()
        for event_item in event_items:
            event = event_item.get("event")
            object = event.get("object")
            method = event.get("method")
            kwargs = event.get("kwargs")
            if object is None:
                continue
            getattr(object, method)(**kwargs)
        return event_items

    def add_exterior_walls(self) -> None:
        """
        Adds exterior walls to the grid.
        This method creates walls around the grid to prevent entities from moving outside the grid.
        """
        self.add_entity(
            StaticEntity(
                name="Left Wall",
                shape=[
                    [0, 0],
                    [0, self.__y_size__],
                    [1 / self.__cell_density__, self.__y_size__],
                    [1 / self.__cell_density__, 0],
                ],
                x_coord=0,
                y_coord=0,
            )
        )

        self.add_entity(
            StaticEntity(
                name="Right Wall",
                shape=[
                    [0, 0],
                    [0, self.__y_size__],
                    [-1 / self.__cell_density__, self.__y_size__],
                    [-1 / self.__cell_density__, 0],
                ],
                x_coord=self.__x_size__,
                y_coord=0,
            )
        )

        self.add_entity(
            StaticEntity(
                name="Top Wall",
                shape=[
                    [0, 0],
                    [self.__x_size__ - 2, 0],
                    [self.__x_size__ - 2, -1 / self.__cell_density__],
                    [0, -1 / self.__cell_density__],
                ],
                x_coord=1,
                y_coord=self.__y_size__,
            )
        )

        self.add_entity(
            StaticEntity(
                name="Bottom Wall",
                shape=[
                    [0, 0],
                    [self.__x_size__ - 2, 0],
                    [self.__x_size__ - 2, 1 / self.__cell_density__],
                    [0, 1 / self.__cell_density__],
                ],
                x_coord=1,
                y_coord=0,
            )
        )

    def simulate(self) -> None:
        """
        Runs the simulation for the grid.
        This method processes events in the queue until all events are resolved or the maximum time is reached.
        """
        next_state_events = True
        while next_state_events:
            next_state_events = self.resolve_next_state()
