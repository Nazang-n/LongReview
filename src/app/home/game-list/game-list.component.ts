import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
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
    imports: [CommonModule, RouterModule, HeaderComponent, FooterComponent, FormsModule],
    templateUrl: './game-list.component.html',
    styleUrls: ['./game-list.component.css']
})
export class GameListComponent implements OnInit {
    isFilterOpen = true;
    allGames: Game[] = [];  // Store all games
    games: Game[] = [];  // Display games (filtered/sorted)
    isLoading = true;
    error: string | null = null;
    searchQuery: string = '';  // Search input

    // Pagination
    currentPage = 1;
    gamesPerPage = 30;
    totalGames = 0;

    constructor(private gameService: GameService) { }

    ngOnInit() {
        this.loadGamesFromDatabase();
    }

    loadGamesFromDatabase() {
        this.isLoading = true;
        this.error = null;

        const skip = (this.currentPage - 1) * this.gamesPerPage;

        // Fetch both games and total count
        forkJoin({
            games: this.gameService.getGames(skip, this.gamesPerPage),
            count: this.gameService.getGamesCount()
        }).subscribe({
            next: ({ games: gamesFromDb, count }) => {
                this.totalGames = count.total;

                if (gamesFromDb && gamesFromDb.length > 0) {
                    // Map database games to display format
                    this.allGames = gamesFromDb.map((game: any) => {
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

                    // Sort games by release date (newest first)
                    this.games.sort((a, b) => {
                        if (!a.releaseDate || a.releaseDate === 'Unknown') return 1;
                        if (!b.releaseDate || b.releaseDate === 'Unknown') return -1;
                        return new Date(b.releaseDate).getTime() - new Date(a.releaseDate).getTime();
                    });
                    // Sort by release date (newest first) when no search
                    this.sortByReleaseDate();

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

    // Pagination methods
    get totalPages(): number {
        return Math.ceil(this.totalGames / this.gamesPerPage);
    }

    get pageNumbers(): number[] {
        const pages: number[] = [];
        const maxPagesToShow = 5;
        let startPage = Math.max(1, this.currentPage - 2);
        let endPage = Math.min(this.totalPages, startPage + maxPagesToShow - 1);

        // Adjust start page if we're near the end
        if (endPage - startPage < maxPagesToShow - 1) {
            startPage = Math.max(1, endPage - maxPagesToShow + 1);
        }

        for (let i = startPage; i <= endPage; i++) {
            pages.push(i);
        }
        return pages;
    }

    goToPage(page: number) {
        if (page >= 1 && page <= this.totalPages) {
            this.currentPage = page;
            this.loadGamesFromDatabase();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }

    previousPage() {
        this.goToPage(this.currentPage - 1);
    }

    nextPage() {
        this.goToPage(this.currentPage + 1);
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

    filterGames() {
        if (!this.searchQuery.trim()) {
            // No search query - show all games sorted by release date
            this.sortByReleaseDate();
            return;
        }

        // Filter games by title (case-insensitive, partial match)
        const query = this.searchQuery.toLowerCase();
        this.games = this.allGames.filter(game =>
            game.title.toLowerCase().includes(query)
        );
    }

    sortByReleaseDate() {
        // Sort by release date (newest first)
        this.games = [...this.allGames].sort((a, b) => {
            const dateA = new Date(a.releaseDate);
            const dateB = new Date(b.releaseDate);
            return dateB.getTime() - dateA.getTime();
        });
    }
}
