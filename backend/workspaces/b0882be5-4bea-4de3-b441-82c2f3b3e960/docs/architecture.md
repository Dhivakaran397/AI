# System Architecture Specification

**Project**: todo
**Target Goal**: **Prompt:**

"Generate a single React functional component named `TodoList` that implements a basic to-do list application.

The component should include the following features:
1.  **State Management:** Use `useState` to manage an array of tasks. Each task object should have an `id`, `text`, and `completed` (boolean) property.
2.  **Add Task:**
    *   An `input` field for entering new task text.
    *   A button to add the task to the list.
    *   Tasks should be added with `completed: false` and a unique `id` (e.g., using `Date.now()`).
    *   The input field should clear after adding a task.
    *   Pressing 'Enter' in the input field should also add the task.
3.  **Delete Task:**
    *   Each task item in the list should have a 'Delete' button.
    *   Clicking 'Delete' removes the corresponding task.
4.  **Toggle Task Completion:**
    *   Clicking on a task's text should toggle its `completed` status.
    *   Completed tasks should have a `line-through` text decoration and a lighter text color.
5.  **Display Tasks:**
    *   Tasks should be displayed in an unordered list (`ul`).
    *   Display a message when there are no tasks.
6.  **Styling:** Apply minimal inline or internal CSS to make the component visually presentable (e.g., basic layout, button styles, completed task styling, input field, and overall container)."

## 1. System Overview
Self-contained reactive single-page architecture with decoupled presentation and state layers.

## 2. Component Structure
- **UI Layer**: Semantic HTML5 with responsive flex/grid styling.
- **Logic Controller**: Interactive JavaScript event loop handling user inputs and state.
- **Validation**: Sanitized input handlers with defensive boundary checking.
