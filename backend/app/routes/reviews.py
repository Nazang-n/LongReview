from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db

router = APIRouter(
    prefix="/api/reviews",
    tags=["reviews"]
)


@router.get("/", response_model=List[schemas.Review])
def get_reviews(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all reviews with pagination."""
    reviews = db.query(models.Review).offset(skip).limit(limit).all()
    return reviews


@router.get("/game/{game_id}", response_model=List[schemas.Review])
def get_reviews_by_game(
    game_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all reviews for a specific game."""
    reviews = db.query(models.Review).filter(
        models.Review.game_id == game_id
    ).offset(skip).limit(limit).all()
    return reviews


@router.get("/{review_id}", response_model=schemas.Review)
def get_review(review_id: int, db: Session = Depends(get_db)):
    """Get a specific review by ID."""
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review with id {review_id} not found"
        )
    return review


@router.post("/", response_model=schemas.Review, status_code=status.HTTP_201_CREATED)
def create_review(review: schemas.ReviewCreate, db: Session = Depends(get_db)):
    """Create a new review."""
    db_review = models.Review(**review.model_dump())
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review


@router.put("/{review_id}", response_model=schemas.Review)
def update_review(
    review_id: int,
    review: schemas.ReviewUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing review."""
    db_review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if db_review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review with id {review_id} not found"
        )
    
    update_data = review.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_review, key, value)
    
    db.commit()
    db.refresh(db_review)
    return db_review


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(review_id: int, db: Session = Depends(get_db)):
    """Delete a review."""
    db_review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if db_review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review with id {review_id} not found"
        )
    
    db.delete(db_review)
    db.commit()
    return None
