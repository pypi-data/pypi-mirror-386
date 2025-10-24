from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any

from gradio.components.base import Component, FormComponent
from gradio.events import Events
from gradio.i18n import I18nData

if TYPE_CHECKING:
    from gradio.components import Timer


class canvaworkflow(FormComponent):
    """
    Custom Gradio component for Canvas Workflow - Visual workflow builder with drag-and-drop functionality.
    """

    EVENTS = [
        Events.change,
        Events.input,
        Events.submit,
    ]

    def __init__(
        self,
        value: dict | Callable | None = None,
        *,
        boxes: list | None = None,
        label_list: str = "Agents",
        label_workflow: str = "Workflow",
        label: str | I18nData | None = None,
        every: Timer | float | None = None,
        inputs: Component | Sequence[Component] | set[Component] | None = None,
        show_label: bool | None = None,
        scale: int | None = None,
        min_width: int = 160,
        interactive: bool | None = None,
        visible: bool = True,
        elem_id: str | None = None,
        elem_classes: list[str] | str | None = None,
        render: bool = True,
        key: int | str | tuple[int | str, ...] | None = None,
        preserved_by_key: list[str] | str | None = "value",
    ):
        """
        Parameters:
            value: default workflow data as a dictionary with 'nodes' and 'connections' keys. If a function is provided, the function will be called each time the app loads to set the initial value of this component.
            boxes: list of available agent/node types that can be dragged to create new nodes.
            label_list: label for the list of draggable items.
            label_workflow: label for the main workflow canvas.
            label: the label for this component, displayed above the component if `show_label` is `True` and is also used as the header if there are a table of examples for this component. If None and used in a `gr.Interface`, the label will be the name of the parameter this component corresponds to.
            every: Continously calls `value` to recalculate it if `value` is a function (has no effect otherwise). Can provide a Timer whose tick resets `value`, or a float that provides the regular interval for the reset Timer.
            inputs: Components that are used as inputs to calculate `value` if `value` is a function (has no effect otherwise). `value` is recalculated any time the inputs change.
            show_label: if True, will display label.
            scale: relative size compared to adjacent Components. For example if Components A and B are in a Row, and A has scale=2, and B has scale=1, A will be twice as wide as B. Should be an integer. scale applies in Rows, and to top-level Components in Blocks where fill_height=True.
            min_width: minimum pixel width, will wrap if not sufficient screen space to satisfy this value. If a certain scale value results in this Component being narrower than min_width, the min_width parameter will be respected first.
            interactive: if True, will be rendered as an editable workflow; if False, editing will be disabled. If not provided, this is inferred based on whether the component is used as an input or output.
            visible: If False, component will be hidden.
            elem_id: An optional string that is assigned as the id of this component in the HTML DOM. Can be used for targeting CSS styles.
            elem_classes: An optional list of strings that are assigned as the classes of this component in the HTML DOM. Can be used for targeting CSS styles.
            render: If False, component will not render be rendered in the Blocks context. Should be used if the intention is to assign event listeners now but render the component later.
            key: in a gr.render, Components with the same key across re-renders are treated as the same component, not a new component. Properties set in 'preserved_by_key' are not reset across a re-render.
            preserved_by_key: A list of parameters from this component's constructor. Inside a gr.render() function, if a component is re-rendered with the same key, these (and only these) parameters will be preserved in the UI (if they have been changed by the user or an event listener) instead of re-rendered based on the values provided during constructor.
        """
        self.boxes = boxes or []
        self.label_list = label_list
        self.label_workflow = label_workflow
        super().__init__(
            label=label,
            every=every,
            inputs=inputs,
            show_label=show_label,
            scale=scale,
            min_width=min_width,
            interactive=interactive,
            visible=visible,
            elem_id=elem_id,
            elem_classes=elem_classes,
            value=value,
            render=render,
            key=key,
            preserved_by_key=preserved_by_key,
        )

    def preprocess(self, payload: dict | None) -> dict | None:
        """
        Parameters:
            payload: the workflow data from the frontend containing nodes and connections.
        Returns:
            Passes workflow data as a {dict} into the function.
        """
        return payload

    def postprocess(self, value: dict | None) -> dict | None:
        """
        Parameters:
            value: Expects a {dict} returned from function with workflow data.
        Returns:
            The workflow data to display in the component.
        """
        return value

    def api_info(self) -> dict[str, Any]:
        """API information for communicating with the frontend"""
        return {
            "type": "object",
            "properties": {
                "nodes": {"type": "array", "items": {"type": "object"}},
                "connections": {"type": "array", "items": {"type": "object"}},
            },
        }

    def example_payload(self) -> Any:
        return {
            "nodes": [
                {"id": "1", "label": "Agent A", "x": 100, "y": 100},
                {"id": "2", "label": "Agent B", "x": 300, "y": 100},
            ],
            "connections": [{"id": "conn_0_1", "from": 0, "to": 1}],
        }

    def example_value(self) -> Any:
        return {
            "nodes": [
                {"id": "1", "label": "Agent A", "x": 100, "y": 100},
                {"id": "2", "label": "Agent B", "x": 300, "y": 100},
            ],
            "connections": [{"id": "conn_0_1", "from": 0, "to": 1}],
        }
