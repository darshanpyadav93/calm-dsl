import ast
import inspect
import uuid

from .entity import EntityType, Entity
from .validator import PropertyValidator
from .task import dag, create_call_rb
from .runbook import runbook_create, runbook
from .node_visitor import GetCallNodes

# Action - Since action, runbook and DAG task are heavily coupled together,
# the action type behaves as all three.


class ActionType(EntityType):
    __schema_name__ = "Action"
    __openapi_type__ = "app_action"

    def __call__(cls, name=None):
        return create_call_rb(cls.runbook, name=name) if cls.runbook else None

    def assign_targets(cls, parent_entity):
        for task in cls.runbook.tasks:
            if not task.target_any_local_reference:
                task.target_any_local_reference = parent_entity.get_task_target()


class ActionValidator(PropertyValidator, openapi_type="app_action"):
    __default__ = None
    __kind__ = ActionType


def _action(**kwargs):
    name = getattr(ActionType, "__schema_name__")
    bases = (Entity,)
    return ActionType(name, bases, kwargs)


Action = _action()


def _action_create(**kwargs):
    name = str(uuid.uuid4())[:8] + "_" + getattr(ActionType, "__schema_name__")
    name = kwargs.get("name", kwargs.get("__name__", name))
    bases = (Action,)
    return ActionType(name, bases, kwargs)


class action(runbook):
    """
    action descriptor
    """

    def __call__(self, name=None):
        return create_call_rb(self.user_runbook, name=name)

    def __get__(self, instance, cls):
        """
        Translate the user defined function to an action.
        Args:
            instance (object): Instance of cls
            cls (Entity): Entity that this action is defined on
        Returns:
            (ActionType): Generated Action class
        """
        if cls is None:
            return self

        if self.__parsed__:
            return self.user_action

        super(action, self).__get__(instance, cls)

        # System action names
        action_name = self.action_name
        ACTION_TYPE = "user"
        func_name = self.user_func.__name__.lower()
        if func_name.startswith("__") and func_name.endswith("__"):
            SYSTEM = getattr(cls, "ALLOWED_SYSTEM_ACTIONS", {})
            FRAGMENT = getattr(cls, "ALLOWED_FRAGMENT_ACTIONS", {})
            if func_name in SYSTEM:
                ACTION_TYPE = "system"
                action_name = SYSTEM[func_name]
            elif func_name in FRAGMENT:
                ACTION_TYPE = "fragment"
                action_name = FRAGMENT[func_name]

        # Finally create the action
        self.user_action = _action_create(
            **{
                "name": action_name,
                "description": self.action_description,
                "critical": ACTION_TYPE == "system",
                "type": ACTION_TYPE,
                "runbook": self.user_runbook,
            }
        )

        self.__parsed__ = True

        return self.user_action


class parallel:
    __calm_type__ = "parallel"
