import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { HeaderComponent } from '../../shared/header.component';
import { FooterComponent } from '../../shared/footer.component';
import { GameService } from '../../services/game.service';
import { FavoriteService } from '../../services/favorite.service';
import { AuthService } from '../../services/auth.service';
import { TagService, TagWithCount } from '../../services/tag.service';
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
    reviewType?: 'positive' | 'negative' | 'mixed';
    isNew?: boolean;
    appId?: string;
    isFavorite?: boolean;
    platform?: string;
    price?: number;
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
    games: Game[] = [];
    paginatedGames: Game[] = []; // Used in template, but now mirrors 'games'
    isLoading = true;
    error: string | null = null;
    searchQuery: string = '';

    // Pagination
    currentPage = 1;
    gamesPerPage = 24; // Better grid layout
    totalGames = 0;

    // Favorites
    userFavoriteIds: number[] = [];

    // Dialog state
    showRemoveDialog = false;
    pendingRemoveGameId: number | null = null;
    pendingRemoveGameTitle: string = '';

    // Filter state
    genres: TagWithCount[] = [];
    platforms: TagWithCount[] = [];
    playerModes: TagWithCount[] = [];
    selectedGenreIds: number[] = [];
    selectedPlatformIds: number[] = [];
    selectedPlayerModeIds: number[] = [];
    expandedSections = {
        platform: true,
        player: true,
        genre: true
    };

    constructor(
        private gameService: GameService,
        private favoriteService: FavoriteService,
        private authService: AuthService,
        private router: Router,
        private tagService: TagService
    ) { }

    ngOnInit() {
        this.loadTags();
        this.loadGames(true); // Initial load
        this.loadUserFavorites();
    }

    loadTags() {
        this.tagService.getTagStats().subscribe({
            next: (response) => {
                this.genres = response.stats.genres.filter(
                    (genre: TagWithCount) => genre.name !== 'Massively Multiplayer' && genre.name !== 'Early Access'
                );
                this.platforms = response.stats.platforms;
                this.playerModes = response.stats.player_modes;
            },
            error: (err) => {
                console.error('Error loading tags:', err);
            }
        });
    }

    toggleSection(section: 'platform' | 'player' | 'genre') {
        this.expandedSections[section] = !this.expandedSections[section];
    }

    toggleGenre(genreId: number) {
        this.toggleFilter(this.selectedGenreIds, genreId);
    }

    togglePlatform(platformId: number) {
        this.toggleFilter(this.selectedPlatformIds, platformId);
    }

    togglePlayerMode(playerModeId: number) {
        this.toggleFilter(this.selectedPlayerModeIds, playerModeId);
    }

    private toggleFilter(array: number[], id: number) {
        const index = array.indexOf(id);
        if (index > -1) {
            array.splice(index, 1);
        } else {
            array.push(id);
        }
        this.applyFilters();
    }

    isGenreSelected(id: number): boolean { return this.selectedGenreIds.includes(id); }
    isPlatformSelected(id: number): boolean { return this.selectedPlatformIds.includes(id); }
    isPlayerModeSelected(id: number): boolean { return this.selectedPlayerModeIds.includes(id); }

    applyFilters() {
        // Reset to page 1 when filtering
        this.loadGames(true);
    }

    loadGames(resetPage: boolean = false) {
        this.isLoading = true;
        this.error = null;

        if (resetPage) {
            this.currentPage = 1;
        }

        // Search mode
        if (this.searchQuery.trim()) {
            this.performSearch();
            return;
        }

        // Standard load mode
        const skip = (this.currentPage - 1) * this.gamesPerPage;
        const tagIds = [...this.selectedGenreIds, ...this.selectedPlatformIds, ...this.selectedPlayerModeIds];

        // 1. Get Count (for pagination)
        this.gameService.getGamesCount(tagIds).subscribe({
            next: (response) => {
                this.totalGames = response.total;
            },
            error: (err) => console.error('Error fetching count:', err)
        });

        // 2. Get Games (for current page)
        this.gameService.getGames(skip, this.gamesPerPage, tagIds).subscribe({
            next: (gamesFromDb) => {
                this.processGamesResponse(gamesFromDb);
                this.isLoading = false;
            },
            error: (err) => {
                console.error('Error loading games:', err);
                this.error = 'Failed to connect to server';
                this.isLoading = false;
                if (this.games.length === 0) this.loadFallbackGames();
            }
        });
    }

    performSearch() {
        const skip = (this.currentPage - 1) * this.gamesPerPage;

        this.gameService.searchGames(this.searchQuery, skip, this.gamesPerPage).subscribe({
            next: (gamesFromDb) => {
                this.processGamesResponse(gamesFromDb);

                // Estimate total for simple pagination
                if (gamesFromDb.length < this.gamesPerPage) {
                    this.totalGames = (this.currentPage - 1) * this.gamesPerPage + gamesFromDb.length;
                } else {
                    // Assume there are more pages
                    this.totalGames = (this.currentPage + 1) * this.gamesPerPage;
                }

                this.isLoading = false;
            },
            error: (err) => {
                console.error('Error searching games:', err);
                this.isLoading = false;
            }
        });
    }

    processGamesResponse(gamesFromDb: any[]) {
        if (gamesFromDb && gamesFromDb.length > 0) {
            this.games = gamesFromDb.map((game: any) => {
                const genres = game.genre ? game.genre.split(',').slice(0, 2).map((g: string) => g.trim()) : [];
                return {
                    id: game.id,
                    title: game.title || 'Unknown Game',
                    description: game.description || game.developer || 'No description available',
                    releaseDate: game.releaseDate || game.release_date || 'Unknown',
                    genres: genres,
                    reviewTags: [],
                    image: game.image_url || `https://via.placeholder.com/460x215?text=${encodeURIComponent(game.title)}`,
                    reviewType: undefined,
                    isNew: false,
                    platform: game.platform,
                    price: game.price
                };
            });

            // Assign to paginatedGames for template compatibility
            this.paginatedGames = this.games;

            // Update favorites
            this.updateFavoriteStatus();

            // Load sentiment for THIS PAGE ONLY
            this.loadGameSentiments();
        } else {
            this.games = [];
            this.paginatedGames = [];
            if (!this.searchQuery) { // Only show fallback if not searching
                this.error = 'No games found.';
            }
        }
    }

    loadFallbackGames() {
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
            }
        ];
        this.paginatedGames = this.games;
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

        if (endPage - startPage < maxPagesToShow - 1) {
            startPage = Math.max(1, endPage - maxPagesToShow + 1);
        }

        endPage = Math.min(endPage, this.totalPages);
        startPage = Math.max(1, startPage);

        for (let i = startPage; i <= endPage; i++) {
            pages.push(i);
        }
        return pages;
    }

    goToPage(page: number) {
        if (page >= 1 && page <= this.totalPages) {
            this.currentPage = page;
            this.loadGames(false); // Load specific page
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
            error: (err) => console.error('Error loading sentiment:', err)
        });
    }

    filterGames() {
        this.currentPage = 1;
        this.loadGames(true);
    }

    loadUserFavorites() {
        const user = this.authService.getCurrentUserValue();
        if (!user) return;

        this.favoriteService.getUserFavorites(user.id).subscribe({
            next: (favorites) => {
                this.userFavoriteIds = favorites.map((f: any) => f.id);
                this.updateFavoriteStatus();
            },
            error: (err) => console.error('Error loading favorites:', err)
        });
    }

    updateFavoriteStatus() {
        this.games.forEach(game => {
            game.isFavorite = this.userFavoriteIds.includes(game.id);
        });
    }

    toggleFavorite(event: Event, game: Game) {
        event.stopPropagation();
        event.preventDefault();

        const user = this.authService.getCurrentUserValue();
        if (!user) {
            this.router.navigate(['/login']);
            return;
        }

        if (game.isFavorite) {
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
                this.games.forEach(g => { if (g.id === gameId) g.isFavorite = false; });
                this.userFavoriteIds = this.userFavoriteIds.filter(id => id !== gameId);
                this.showRemoveDialog = false;
                this.pendingRemoveGameId = null;
            },
            error: (err) => {
                console.error('Error removing favorite:', err);
                this.showRemoveDialog = false;
            }
        });
    }

    cancelRemove() {
        this.showRemoveDialog = false;
        this.pendingRemoveGameId = null;
    }
}
