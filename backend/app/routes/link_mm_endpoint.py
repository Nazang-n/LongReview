@router.post("/link-mm-to-multiplayer")
def link_massively_multiplayer_to_multiplayer(db: Session = Depends(get_db)):
    """
    Link all games with 'Massively Multiplayer' genre to 'Multi-player' player mode tag.
    
    This is useful because Massively Multiplayer games are inherently multiplayer games,
    so they should appear in the Multi-player filter.
    """
    try:
        # Find Massively Multiplayer genre tag
        mm_genre_tag = db.query(models.Tag).filter(
            models.Tag.name == 'Massively Multiplayer',
            models.Tag.type == 'genre'
        ).first()
        
        if not mm_genre_tag:
            return {
                "success": False,
                "message": "Massively Multiplayer genre tag not found"
            }
        
        # Find or create Multi-player tag
        multiplayer_tag = db.query(models.Tag).filter(
            models.Tag.name == 'Multi-player',
            models.Tag.type == 'player_mode'
        ).first()
        
        if not multiplayer_tag:
            multiplayer_tag = models.Tag(name='Multi-player', type='player_mode')
            db.add(multiplayer_tag)
            db.flush()
        
        # Find all games with Massively Multiplayer genre
        mm_game_tags = db.query(models.GameTag).filter(
            models.GameTag.tag_id == mm_genre_tag.id
        ).all()
        
        linked_count = 0
        already_linked_count = 0
        
        for game_tag in mm_game_tags:
            game_id = game_tag.game_id
            
            # Check if already linked to Multi-player
            existing_link = db.query(models.GameTag).filter(
                models.GameTag.game_id == game_id,
                models.GameTag.tag_id == multiplayer_tag.id
            ).first()
            
            if existing_link:
                already_linked_count += 1
            else:
                # Create link
                new_link = models.GameTag(
                    game_id=game_id,
                    tag_id=multiplayer_tag.id
                )
                db.add(new_link)
                linked_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Linked {linked_count} Massively Multiplayer games to Multi-player tag",
            "newly_linked": linked_count,
            "already_linked": already_linked_count,
            "total_mm_games": len(mm_game_tags)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error linking tags: {str(e)}"
        )
