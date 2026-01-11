from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from .. import models
from ..database import get_db

router = APIRouter(
    prefix="/api/comments",
    tags=["comments"]
)


# Pydantic models for request/response
class CommentCreate(BaseModel):
    """Request body for creating a comment"""
    user_id: int
    content: str


class CommentUpdate(BaseModel):
    """Request body for updating a comment"""
    user_id: int
    content: str


class LikeRequest(BaseModel):
    """Request body for liking a comment"""
    user_id: int


class ReportRequest(BaseModel):
    """Request body for reporting a comment"""
    user_id: int
    reason: str


class CommentResponse(BaseModel):
    """Response model for a comment"""
    id: int
    game_id: int
    user_id: int
    username: str
    content: str
    is_edited: bool
    created_at: str
    updated_at: str
    upvotes: int


class ReportResponse(BaseModel):
    """Response model for a comment report"""
    id: int
    comment_id: int
    comment_content: str
    game_id: int
    game_title: str
    reporter_id: int
    reporter_username: str
    reason: str
    status: str
    created_at: str


@router.post("/{game_id}", status_code=status.HTTP_201_CREATED)
def add_comment(
    game_id: int,
    request: CommentCreate,
    db: Session = Depends(get_db)
):
    """
    Add a new comment to a game.
    
    - **game_id**: The ID of the game
    - **user_id**: The ID of the user posting the comment
    - **content**: The comment text
    """
    # Verify game exists
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game with id {game_id} not found"
        )
    
    # Verify user exists
    user = db.query(models.User).filter(models.User.id == request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {request.user_id} not found"
        )
    
    # Create comment
    new_comment = models.Comment(
        game_id=game_id,
        user_id=request.user_id,
        content=request.content,
        upvotes=0
    )
    
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    
    return {
        "success": True,
        "message": "Comment added successfully",
        "comment_id": new_comment.id
    }


@router.get("/{game_id}")
def get_comments(
    game_id: int,
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get all comments for a game.
    
    - **game_id**: The ID of the game
    - **user_id**: Optional - not used anymore (kept for compatibility)
    """
    comments = db.query(models.Comment).filter(
        models.Comment.game_id == game_id
    ).order_by(models.Comment.created_at.desc()).all()
    
    result = []
    for comment in comments:
        # Get username
        user = db.query(models.User).filter(models.User.id == comment.user_id).first()
        username = user.username if user else "Unknown User"
        
        result.append({
            "id": comment.id,
            "game_id": comment.game_id,
            "user_id": comment.user_id,
            "username": username,
            "content": comment.content,
            "is_edited": comment.is_edited,
            "created_at": comment.created_at.isoformat() if comment.created_at else None,
            "updated_at": comment.updated_at.isoformat() if comment.updated_at else None,
            "upvotes": comment.upvotes
        })
    
    return result


@router.put("/{comment_id}")
def edit_comment(
    comment_id: int,
    request: CommentUpdate,
    db: Session = Depends(get_db)
):
    """
    Edit a comment (only by the comment owner).
    
    - **comment_id**: The ID of the comment to edit
    - **user_id**: The ID of the user (must be comment owner)
    - **content**: The new comment text
    """
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    # Verify ownership
    if comment.user_id != request.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own comments"
        )
    
    # Update comment
    comment.content = request.content
    comment.is_edited = True
    comment.updated_at = datetime.now()
    
    db.commit()
    
    return {
        "success": True,
        "message": "Comment updated successfully"
    }


@router.delete("/{comment_id}")
def delete_comment(
    comment_id: int,
    user_id: int = Query(...),
    db: Session = Depends(get_db)
):
    """
    Delete a comment (by owner or admin).
    
    - **comment_id**: The ID of the comment to delete
    - **user_id**: The ID of the user
    """
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    # Get user
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user is owner or admin
    is_owner = comment.user_id == user_id
    is_admin = user.user_role == "Admin"
    
    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own comments"
        )
    
    # Delete related reports
    db.query(models.CommentReport).filter(
        models.CommentReport.comment_id == comment_id
    ).delete()
    
    # Delete comment
    db.delete(comment)
    db.commit()
    
    return {
        "success": True,
        "message": "Comment deleted successfully"
    }


@router.post("/{comment_id}/like")
def like_comment(
    comment_id: int,
    request: LikeRequest,
    db: Session = Depends(get_db)
):
    """
    Like a comment (increment upvotes).
    
    - **comment_id**: The ID of the comment
    - **user_id**: The ID of the user liking
    """
    # Verify comment exists
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    # Increment upvotes
    comment.upvotes += 1
    db.commit()
    
    return {
        "success": True,
        "message": "Comment liked",
        "upvotes": comment.upvotes
    }


@router.post("/{comment_id}/report")
def report_comment(
    comment_id: int,
    request: ReportRequest,
    db: Session = Depends(get_db)
):
    """
    Report a comment for inappropriate content.
    
    - **comment_id**: The ID of the comment to report
    - **user_id**: The ID of the user reporting
    - **reason**: The reason for reporting
    """
    # Verify comment exists
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    # Check if user already reported this comment
    existing_report = db.query(models.CommentReport).filter(
        and_(
            models.CommentReport.comment_id == comment_id,
            models.CommentReport.reporter_id == request.user_id,
            models.CommentReport.status == 'pending'
        )
    ).first()
    
    if existing_report:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reported this comment"
        )
    
    # Create report
    new_report = models.CommentReport(
        comment_id=comment_id,
        reporter_id=request.user_id,
        reason=request.reason,
        status='pending'
    )
    
    db.add(new_report)
    db.commit()
    
    return {
        "success": True,
        "message": "Comment reported successfully"
    }


@router.get("/reports/all")
def get_all_reports(
    user_id: int = Query(...),
    db: Session = Depends(get_db)
):
    """
    Get all pending comment reports (admin only).
    
    - **user_id**: The ID of the user (must be admin)
    """
    # Verify user is admin
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or user.user_role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get all pending reports
    reports = db.query(models.CommentReport).filter(
        models.CommentReport.status == 'pending'
    ).order_by(models.CommentReport.created_at.desc()).all()
    
    result = []
    for report in reports:
        # Get comment
        comment = db.query(models.Comment).filter(
            models.Comment.id == report.comment_id
        ).first()
        
        if not comment:
            continue
        
        # Get game
        game = db.query(models.Game).filter(
            models.Game.id == comment.game_id
        ).first()
        
        # Get reporter
        reporter = db.query(models.User).filter(
            models.User.id == report.reporter_id
        ).first()
        
        result.append({
            "id": report.id,
            "comment_id": report.comment_id,
            "comment_content": comment.content,
            "comment_user_id": comment.user_id,
            "game_id": comment.game_id,
            "game_title": game.title if game else "Unknown",
            "reporter_id": report.reporter_id,
            "reporter_username": reporter.username if reporter else "Unknown",
            "reason": report.reason,
            "status": report.status,
            "created_at": report.created_at.isoformat() if report.created_at else None
        })
    
    return result


@router.put("/reports/{report_id}/dismiss")
def dismiss_report(
    report_id: int,
    user_id: int = Query(...),
    db: Session = Depends(get_db)
):
    """
    Dismiss a comment report (admin only).
    
    - **report_id**: The ID of the report to dismiss
    - **user_id**: The ID of the admin user
    """
    # Verify user is admin
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or user.user_role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get report
    report = db.query(models.CommentReport).filter(
        models.CommentReport.id == report_id
    ).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    # Update report
    report.status = 'dismissed'
    # report.reviewed_by = user_id
    # report.reviewed_at = datetime.now()
    
    db.commit()
    
    return {
        "success": True,
        "message": "Report dismissed successfully"
    }
