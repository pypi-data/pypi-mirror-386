import asyncio
from typing import Tuple, override
from PySide6 import QtCore, QtWidgets, QtGui

from orcalab.actor import BaseActor, GroupActor
from orcalab.local_scene import LocalScene
from orcalab.path import Path
from orcalab.pyside_util import connect
from orcalab.scene_edit_bus import (
    SceneEditRequestBus,
    SceneEditNotification,
    SceneEditNotificationBus,
    get_actor_and_path,
    make_unique_name,
    can_rename_actor,
)

from orcalab.ui.actor_outline_model import ActorOutlineModel
from orcalab.ui.rename_dialog import RenameDialog


class ActorOutlineDelegate(QtWidgets.QStyledItemDelegate):

    def __init__(self, /, parent=...):
        super().__init__(parent)

    # @typing.override
    # def createEditor(self, parent, option, index):
    #     return QtWidgets.QLineEdit(text="aaaa", parent=parent)

    # def setEditorData(self, editor: QtWidgets.QLineEdit, index):
    #     print("set data")

    # def updateEditorGeometry(
    #     self, editor: QtWidgets.QLineEdit, option: QtWidgets.QStyleOptionViewItem, index
    # ):
    #     print(option.rect)
    #     editor.setGeometry(option.rect)

    # def setModelData(self, editor: QtWidgets.QLineEdit, model, index):
    #     print(editor.text())


# QTreeView的默认行为是按下鼠标左键时选中，我们希望在鼠标左键抬起的时候选中。
# 这样可以避免在拖拽时选中。
class ActorOutline(QtWidgets.QTreeView, SceneEditNotification):

    def __init__(self):
        super().__init__()
        self.setHeaderHidden(True)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.setItemDelegate(ActorOutlineDelegate(self))

        # self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(QtCore.Qt.DropAction.CopyAction)

        self._change_from_inside = False
        self._change_from_outside = False
        self._current_index = QtCore.QModelIndex()
        self._current_actor: BaseActor | None = None

        self._brach_areas = {}
        self._left_mouse_pressed = False

        self.reparent_mime = "application/x-orca-actor-reparent"

    def connect_bus(self):
        SceneEditNotificationBus.connect(self)

    def disconnect_bus(self):
        SceneEditNotificationBus.disconnect(self)

    def set_actor_model(self, model: ActorOutlineModel):
        self.setModel(model)
        self.selectionModel().selectionChanged.connect(self._on_selection_changed)
        connect(model.request_reparent, self._on_request_reparent)

    async def _on_request_reparent(
        self, actor_path: Path, new_parent_path: Path, index: int
    ):
        print(f"reparent {actor_path} to {new_parent_path} at {index}")
        await SceneEditRequestBus().reparent_actor(
            actor_path, new_parent_path, index, undo=True, source="actor_outline"
        )

    @QtCore.Slot()
    def _on_selection_changed(self):
        if self._change_from_outside:
            return

        self._change_from_inside = True

        actors = []
        indexes = self.selectedIndexes()
        for index in indexes:
            actor = index.internalPointer()
            if not isinstance(actor, BaseActor):
                raise Exception("Invalid actor.")
            actors.append(actor)

        asyncio.create_task(
            SceneEditRequestBus().set_selection(
                actors, undo=True, source="actor_outline"
            )
        )

        self._change_from_inside = False

    @override
    async def on_selection_changed(self, old_selection, new_selection, source=""):
        if source == "actor_outline":
            return

        actors = []

        for actor_path in new_selection:
            actor, actor_path = get_actor_and_path(actor_path)
            actors.append(actor)

        self.set_actor_selection(actors)

    def set_actor_selection(self, actors: list[BaseActor]):
        if self._change_from_inside:
            return

        self._change_from_outside = True

        selection_model = self.selectionModel()
        selection_model.clearSelection()

        model: ActorOutlineModel = self.model()
        for actor in actors:
            index = model.get_index_from_actor(actor)
            if not index.isValid():
                raise Exception("Invalid actor.")

            selection_model.select(
                index, QtCore.QItemSelectionModel.SelectionFlag.Select
            )
            self.scrollTo(index)

        self._change_from_outside = False

    @QtCore.Slot()
    def show_context_menu(self, position):
        self._current_index = self.indexAt(position)

        actor_outline_model: ActorOutlineModel = self.model()
        local_scene: LocalScene = actor_outline_model.local_scene

        is_root = False
        current_actor = actor_outline_model.get_actor(self._current_index)
        if current_actor is None:
            current_actor = local_scene.root_actor
            is_root = True

        self._current_actor = current_actor
        self._current_actor_path = local_scene.get_actor_path(self._current_actor)

        menu = QtWidgets.QMenu()

        action_add_group = QtGui.QAction("Add Group")
        connect(action_add_group.triggered, self._add_group)
        menu.addAction(action_add_group)

        if self._current_index.isValid():
            menu.addSeparator()

            action_delete = QtGui.QAction("Delete")
            connect(action_delete.triggered, self._delete_actor)
            action_delete.setEnabled(not is_root)
            menu.addAction(action_delete)

            action_rename = QtGui.QAction("Rename")
            connect(action_rename.triggered, self._open_rename_dialog)
            action_rename.setEnabled(not is_root)
            menu.addAction(action_rename)

        menu.exec_(self.mapToGlobal(position))

    async def _add_group(self):
        parent_actor = self._current_actor
        parent_actor_path = self._current_actor_path
        if not isinstance(parent_actor, GroupActor):
            parent_actor = parent_actor.parent
            parent_actor_path = parent_actor_path.parent()

        assert isinstance(parent_actor, GroupActor)

        new_group_name = make_unique_name("group", parent_actor)
        actor = GroupActor(name=new_group_name)

        await SceneEditRequestBus().add_actor(
            actor, parent_actor, undo=True, source="actor_outline"
        )

    async def _delete_actor(self):
        await SceneEditRequestBus().delete_actor(
            self._current_actor, undo=True, source="actor_outline"
        )

    def _open_rename_dialog(self):
        dialog = RenameDialog(self._current_actor_path, can_rename_actor, self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            asyncio.create_task(
                SceneEditRequestBus().rename_actor(
                    self._current_actor,
                    dialog.new_name,
                    undo=True,
                    source="actor_outline",
                )
            )

    def _get_actor_at_pos(self, pos) -> Tuple[BaseActor, Path]:
        index = self.indexAt(pos)
        actor_outline_model: ActorOutlineModel = self.model()
        actor = actor_outline_model.get_actor(index)
        if actor is None:
            raise Exception("Invalid actor.")

        return actor_outline_model.local_scene.get_actor_and_path(actor)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton:
            self._left_mouse_pressed = True
            actor, actor_path = self._get_actor_at_pos(event.pos())
            self._current_actor = actor
            self._current_actor_path = actor_path

            self.startDrag(QtCore.Qt.DropActions(QtCore.Qt.DropAction.CopyAction))

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton:
            if not self._left_mouse_pressed:
                return

            self._left_mouse_pressed = False

            pos = event.position().toPoint()
            index = self.indexAt(pos)
            actor, actor_path = self._get_actor_at_pos(pos)

            if actor_path == Path.root_path():
                self.set_actor_selection([])

                asyncio.create_task(
                    SceneEditRequestBus().set_selection(
                        [], undo=True, source="actor_outline"
                    )
                )

            else:
                rect = self._brach_areas.get(index)

                if rect and rect.contains(pos):
                    self.setExpanded(index, not self.isExpanded(index))
                else:
                    self.set_actor_selection([actor])
                    asyncio.create_task(
                        SceneEditRequestBus().set_selection(
                            [actor], undo=True, source="actor_outline"
                        )
                    )

    def mouseMoveEvent(self, event):
        if self._left_mouse_pressed:
            self._left_mouse_pressed = False

            data = self._current_actor_path.string().encode("utf-8")

            mime_data = QtCore.QMimeData()
            mime_data.setData("application/x-orca-actor-reparent", data)

            drag = QtGui.QDrag(self)
            drag.setMimeData(mime_data)
            drag.exec(QtCore.Qt.DropAction.CopyAction)

    def paintEvent(self, event):
        self._brach_areas = {}
        return super().paintEvent(event)

    def drawBranches(self, painter, rect, index):
        self._brach_areas[index] = rect
        return super().drawBranches(painter, rect, index)


if __name__ == "__main__":
    import sys
    from actor_outline_model import ActorOutlineModel
    from orcalab.actor import GroupActor, AssetActor

    app = QtWidgets.QApplication(sys.argv)

    local_scene = LocalScene()
    local_scene.add_actor(GroupActor("g1"), Path("/"))
    local_scene.add_actor(GroupActor("g2"), Path("/"))
    local_scene.add_actor(GroupActor("g3"), Path("/"))
    local_scene.add_actor(GroupActor("g4"), Path("/g2"))
    local_scene.add_actor(AssetActor("a1", "spw_name"), Path("/g3"))

    model = ActorOutlineModel(local_scene)
    model.set_root_group(local_scene.root_actor)

    def on_request_reparent(actor_path: Path, new_parent_path: Path, row: int):
        if row < 0:
            print(f"reparent {actor_path} to end of {new_parent_path}")
        else:
            print(f"reparent {actor_path} to row {row} of {new_parent_path}")

    model.request_reparent.connect(on_request_reparent)

    actor_outline = ActorOutline()
    actor_outline.set_actor_model(model)
    actor_outline.show()

    app.exec()
