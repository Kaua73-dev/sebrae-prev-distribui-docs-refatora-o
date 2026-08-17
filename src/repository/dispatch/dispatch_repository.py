from sqlalchemy.orm import Session, joinedload

from src.model.dispatch import BlockStatus, Dispatch, DispatchBlock


class DispatchRepository:

    def __init__(self, db: Session):
        self.db = db

    def save(self, dispatch: Dispatch) -> Dispatch:
        self.db.add(dispatch)
        self.db.commit()
        self.db.refresh(dispatch)
        return dispatch

    def save_block(self, block: DispatchBlock) -> DispatchBlock:
        self.db.add(block)
        self.db.commit()
        self.db.refresh(block)
        return block

    def find_by_id(self, dispatch_id: int) -> Dispatch | None:
        return (
            self.db.query(Dispatch)
            .options(joinedload(Dispatch.blocks))
            .filter(Dispatch.id == dispatch_id)
            .first()
        )

    def find_all(self) -> list[Dispatch]:
        return (
            self.db.query(Dispatch)
            .order_by(Dispatch.create_at.desc())
            .all()
        )

    def find_blocks_to_send(self, dispatch_id: int) -> list[DispatchBlock]:
        return (
            self.db.query(DispatchBlock)
            .filter(
                DispatchBlock.dispatch_id == dispatch_id,
                DispatchBlock.included.is_(True),
                DispatchBlock.status != BlockStatus.SENT,
            )
            .order_by(DispatchBlock.prefix_name.asc())
            .all()
        )
