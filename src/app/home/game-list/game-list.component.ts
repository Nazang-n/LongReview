import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { HeaderComponent } from '../../shared/header.component';
import { FooterComponent } from '../../shared/footer.component';
import { GameService } from '../../services/game.service';
import { forkJoin } from 'rxjs';

interface Game {
    id: number;
    title: string;
    description: string;
    releaseDate: string;
    genres: string[];
    reviewTags: string[];
    image: string;
    reviewType?: 'positive' | 'negative' | 'mixed';  // Optional - set by sentiment data
    isNew?: boolean;
    appId?: string;
}

@Component({
    selector: 'app-game-list',
    standalone: true,
    imports: [CommonModule, RouterModule, HeaderComponent, FooterComponent],
    templateUrl: './game-list.component.html',
    styleUrls: ['./game-list.component.css']
})
export class GameListComponent implements OnInit {
    isFilterOpen = true;
    games: Game[] = [];
    isLoading = true;
    error: string | null = null;

    constructor(private gameService: GameService) { }

    ngOnInit() {
        this.loadGamesFromDatabase();
    }

    loadGamesFromDatabase() {
        this.isLoading = true;
        this.error = null;

        // Fetch games from local database (already imported from SteamSpy + Steam API)
        this.gameService.getGames(0, 30).subscribe({
            next: (gamesFromDb) => {
                if (gamesFromDb && gamesFromDb.length > 0) {
                    // Map database games to display format
                    this.games = gamesFromDb.map((game: any) => {
                        // Extract genres
                        const genres = game.genre ? game.genre.split(',').slice(0, 2).map((g: string) => g.trim()) : [];

                        return {
                            id: game.id,
                            title: game.title || 'Unknown Game',
                            description: game.description || game.developer || 'No description available',
                            releaseDate: game.release_date || 'Unknown',
                            genres: genres,
                            reviewTags: [],
                            image: game.image_url || `https://via.placeholder.com/460x215?text=${encodeURIComponent(game.title)}`,
                            reviewType: undefined,  // Will be set by loadGameSentiments()
                            isNew: false,
                            platform: game.platform,
                            price: game.price
                        };
                    });

                    this.isLoading = false;

                    // Load sentiment data for review badges
                    this.loadGameSentiments();
                } else {
                    // No games in database - show message
                    this.error = 'No games found in database. Please import games first using: POST /api/steam/steamspy/import/batch';
                    this.isLoading = false;
                    this.loadFallbackGames();
                }
            },
            error: (err) => {
                console.error('Error loading games from database:', err);
                this.error = 'Failed to connect to server';
                this.isLoading = false;
                this.loadFallbackGames();
            }
        });
    }

    loadFallbackGames() {
        // Fallback to hardcoded games if API fails
        this.games = [
            {
                id: 1,
                title: 'Apex Legends',
                description: 'เกมที่ผสมผสาน Battle Royale ที่มีตัวละครที่แตกต่างกัน',
                releaseDate: '4 ตุลาคม 2562',
                genres: ['Battle Royale', 'FPS'],
                reviewTags: ['ยิงปืน', 'เกมไว'],
                image: 'https://cdn.cloudflare.steamstatic.com/steam/apps/1172470/header.jpg',
                reviewType: 'positive',
                isNew: false
            },
            {
                id: 2,
                title: 'Counter-Strike 2',
                description: 'เกม FPS ที่ได้รับความนิยมสูงสุดในโลก',
                releaseDate: '2023',
                genres: ['FPS', 'Multiplayer'],
                reviewTags: ['แข่งขัน', 'ยิงปืน'],
                image: 'https://cdn.cloudflare.steamstatic.com/steam/apps/730/header.jpg',
                reviewType: 'positive',
                isNew: false
            },
            {
                id: 3,
                title: 'Dota 2',
                description: 'เกม MOBA ที่มีผู้เล่นมากที่สุดบน Steam',
                releaseDate: '2013',
                genres: ['MOBA', 'Strategy'],
                reviewTags: ['แข่งขัน', 'ทีมเวิร์ค'],
                image: 'https://cdn.cloudflare.steamstatic.com/steam/apps/570/header.jpg',
                reviewType: 'positive',
                isNew: false
            }
        ];
    }

    toggleFilter() {
        this.isFilterOpen = !this.isFilterOpen;
    }

    loadGameSentiments() {
        const gameIds = this.games.map(g => g.id);

        if (gameIds.length === 0) return;

        this.gameService.getBatchSentiment(gameIds).subscribe({
            next: (sentiments) => {
                this.games.forEach(game => {
                    const sentiment = sentiments[game.id];
                    if (sentiment) {
                        const diff = Math.abs(sentiment.positive_percent - sentiment.negative_percent);

                        // Determine review type based on percentages
                        if (diff <= 10) {
                            game.reviewType = 'mixed';
                        } else if (sentiment.positive_percent > sentiment.negative_percent) {
                            game.reviewType = 'positive';
                        } else {
                            game.reviewType = 'negative';
                        }
                    }
                });
            },
            error: (err) => {
                console.error('Error loading sentiment data:', err);
            }
        });
    }
}
