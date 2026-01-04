import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { HeaderComponent } from '../../shared/header.component';
import { FooterComponent } from '../../shared/footer.component';
import { GameService } from '../../services/game.service';
import { FavoriteService } from '../../services/favorite.service';
import { AuthService } from '../../services/auth.service';
import { DialogModule } from 'primeng/dialog';
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
    isFavorite?: boolean;  // Is this game in user's favorites?
}

@Component({
    selector: 'app-game-list',
    standalone: true,
    imports: [CommonModule, RouterModule, HeaderComponent, FooterComponent, FormsModule, DialogModule],
    templateUrl: './game-list.component.html',
    styleUrls: ['./game-list.component.css']
})
export class GameListComponent implements OnInit {
    isFilterOpen = true;
    allGames: Game[] = [];  // Store all games
    games: Game[] = [];  // Filtered games (after search)
    paginatedGames: Game[] = [];  // Games to display on current page
    isLoading = true;
    error: string | null = null;
    searchQuery: string = '';  // Search input

    // Pagination
    currentPage = 1;
    gamesPerPage = 12;  // Show 12 games per page
    totalGames = 0;

    // Favorites
    userFavoriteIds: number[] = [];  // IDs of user's favorite games

    // Dialog state
    showRemoveDialog = false;
    pendingRemoveGameId: number | null = null;
    pendingRemoveGameTitle: string = '';

    constructor(
        private gameService: GameService,
        private favoriteService: FavoriteService,
        private authService: AuthService,
        private router: Router
    ) { }

    ngOnInit() {
        this.loadGamesFromDatabase();
        this.loadUserFavorites();
    }

    loadGamesFromDatabase() {
        this.isLoading = true;
        this.error = null;

        // Load ALL games at once (no pagination from backend)
        this.gameService.getGames(0, 1000).subscribe({  // Load up to 1000 games
            next: (gamesFromDb) => {
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

                    this.totalGames = this.allGames.length;

                    // Sort by release date (newest first)
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
            error: (err: any) => {
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
        return Math.ceil(this.games.length / this.gamesPerPage);
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
            this.getPaginatedGames();  // Get paginated slice
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

        // Reset to page 1 and paginate
        this.currentPage = 1;
        this.getPaginatedGames();
    }

    sortByReleaseDate() {
        // Sort by release date (newest first)
        this.games = [...this.allGames].sort((a, b) => {
            const dateA = new Date(a.releaseDate);
            const dateB = new Date(b.releaseDate);
            return dateB.getTime() - dateA.getTime();
        });

        // Paginate after sorting
        this.getPaginatedGames();
    }

    getPaginatedGames() {
        const start = (this.currentPage - 1) * this.gamesPerPage;
        const end = start + this.gamesPerPage;
        this.paginatedGames = this.games.slice(start, end);
    }

    loadUserFavorites() {
        const user = this.authService.getCurrentUserValue();
        if (!user) return;

        this.favoriteService.getUserFavorites(user.id).subscribe({
            next: (favorites) => {
                this.userFavoriteIds = favorites.map((f: any) => f.id);
                this.updateFavoriteStatus();
            },
            error: (err: any) => {
                console.error('Error loading user favorites:', err);
            }
        });
    }

    updateFavoriteStatus() {
        // Update favorite status for all game arrays
        this.allGames.forEach(game => {
            game.isFavorite = this.userFavoriteIds.includes(game.id);
        });
        this.games.forEach(game => {
            game.isFavorite = this.userFavoriteIds.includes(game.id);
        });
        this.paginatedGames.forEach(game => {
            game.isFavorite = this.userFavoriteIds.includes(game.id);
        });
    }

    toggleFavorite(event: Event, game: Game) {
        event.stopPropagation();  // Prevent navigation to game detail
        event.preventDefault();

        const user = this.authService.getCurrentUserValue();
        if (!user) {
            this.router.navigate(['/login']);
            return;
        }

        if (game.isFavorite) {
            // Show confirmation dialog
            this.pendingRemoveGameId = game.id;
            this.pendingRemoveGameTitle = game.title;
            this.showRemoveDialog = true;
        }
    }

    confirmRemove() {
        const user = this.authService.getCurrentUserValue();
        if (!user || !this.pendingRemoveGameId) return;

        this.favoriteService.removeFavorite(user.id, this.pendingRemoveGameId).subscribe({
            next: () => {
                const gameId = this.pendingRemoveGameId;
                this.allGames.forEach(g => { if (g.id === gameId) g.isFavorite = false; });
                this.games.forEach(g => { if (g.id === gameId) g.isFavorite = false; });
                this.paginatedGames.forEach(g => { if (g.id === gameId) g.isFavorite = false; });

                this.userFavoriteIds = this.userFavoriteIds.filter(id => id !== gameId);
                this.showRemoveDialog = false;
                this.pendingRemoveGameId = null;
                this.pendingRemoveGameTitle = '';
            },
            error: (err: any) => {
                console.error('Error removing favorite:', err);
                this.showRemoveDialog = false;
            }
        });
    }

    cancelRemove() {
        this.showRemoveDialog = false;
        this.pendingRemoveGameId = null;
        this.pendingRemoveGameTitle = '';
    }
}
