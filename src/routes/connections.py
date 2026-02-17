from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from src.config.database import get_db
from src.models import Connection, User, ConnectionStatus
from src.schemas.connection import ConnectionCreate, ConnectionRead, ConnectionUpdate
from src.routes.users import get_current_user
from src.routes.notifications import create_notification_internal

router = APIRouter(prefix="/connections", tags=["Connections"])

@router.post("/", response_model=ConnectionRead, status_code=status.HTTP_201_CREATED)
def send_connection_request(
    payload: ConnectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.recipient_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot connect with yourself")

    recipient = db.query(User).filter(User.id == payload.recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="User not found")

    existing = db.query(Connection).filter(
        ((Connection.requester_id == current_user.id) & (Connection.recipient_id == payload.recipient_id)) |
        ((Connection.requester_id == payload.recipient_id) & (Connection.recipient_id == current_user.id))
    ).first()

    if existing:
        if existing.status == ConnectionStatus.PENDING:
            raise HTTPException(status_code=400, detail="Connection request already pending")
        elif existing.status == ConnectionStatus.ACCEPTED:
            raise HTTPException(status_code=400, detail="Already connected")
        elif existing.status == ConnectionStatus.REJECTED:
             # Allow re-requesting if rejected? For now, yes, maybe update status to pending.
             existing.status = ConnectionStatus.PENDING
             existing.requester_id = current_user.id # Reset requester
             existing.recipient_id = payload.recipient_id
             db.commit()
             db.refresh(existing)
             return existing
        
    new_connection = Connection(
        requester_id=current_user.id,
        recipient_id=payload.recipient_id,
        status=ConnectionStatus.PENDING
    )
    db.add(new_connection)
    db.commit()
    db.refresh(new_connection)
    
    # Notify recipient
    create_notification_internal(
        db=db,
        recipient_id=payload.recipient_id,
        type="connection_request",
        content=f"{current_user.name} sent you a connection request.",
        related_entity_id=new_connection.id
    )
    
    return new_connection

@router.delete("/{connection_id}/cancel", status_code=status.HTTP_204_NO_CONTENT)
def cancel_connection_request(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    connection = db.query(Connection).filter(
        Connection.id == connection_id,
        Connection.requester_id == current_user.id,
        Connection.status == ConnectionStatus.PENDING
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Pending connection request not found")
        
    db.delete(connection)
    db.commit()

@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_connection(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Allow removing if user is either requester or recipient
    connection = db.query(Connection).filter(
        Connection.id == connection_id,
        ((Connection.requester_id == current_user.id) | (Connection.recipient_id == current_user.id))
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
        
    db.delete(connection)
    db.commit()

@router.get("/requests", response_model=List[ConnectionRead])
def get_pending_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Connection).filter(
        Connection.recipient_id == current_user.id,
        Connection.status == ConnectionStatus.PENDING
    ).all()

@router.put("/{connection_id}", response_model=ConnectionRead)
def update_connection_status(
    connection_id: int,
    payload: ConnectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    connection = db.query(Connection).filter(Connection.id == connection_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    if connection.recipient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this connection")

    if payload.status not in [ConnectionStatus.ACCEPTED, ConnectionStatus.REJECTED]:
         raise HTTPException(status_code=400, detail="Invalid status update")

    connection.status = payload.status
    db.commit()
    db.refresh(connection)
    return connection

@router.get("/", response_model=List[ConnectionRead])
def get_connections(
    type: str = Query("accepted", regex="^(accepted|pending|sent)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Connection)
    
    if type == "accepted":
        query = query.filter(
            ((Connection.requester_id == current_user.id) | (Connection.recipient_id == current_user.id)),
            Connection.status == ConnectionStatus.ACCEPTED
        )
    elif type == "pending":
        # Received Pending Requests
        query = query.filter(
            Connection.recipient_id == current_user.id,
            Connection.status == ConnectionStatus.PENDING
        )
    elif type == "sent":
        # Sent Pending Requests
        query = query.filter(
            Connection.requester_id == current_user.id,
            Connection.status == ConnectionStatus.PENDING
        )
        
    return query.all()
