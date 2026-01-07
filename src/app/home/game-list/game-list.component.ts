import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { HeaderComponent } from '../../shared/header.component';
import { FooterComponent } from '../../shared/footer.component';
import { GameService } from '../../services/game.service';
import { FavoriteService } from '../../services/favorite.service';
import { AuthService } from '../../services/auth.service';
import { TagService, TagWithCount } from '../../services/tag.service'; // Added Back for Sidebar
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
    allGames: Game[] = [];  // Store all games
    games: Game[] = [];  // Filtered games (after search)
    paginatedGames: Game[] = []; // Games to display on current page
    isLoading = true;
    error: string | null = null;
    searchQuery: string = '';

    // Favorites
    userFavoriteIds: number[] = [];

    // Dialog state
    showRemoveDialog = false;
    pendingRemoveGameId: number | null = null;
    pendingRemoveGameTitle: string = '';

    // Filter state (kept for Sidebar compatibility)
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

    // Pagination
    currentPage = 1;
    gamesPerPage = 24;
    totalGames = 0;

    constructor(
        private gameService: GameService,
        private favoriteService: FavoriteService,
        private authService: AuthService,
        private router: Router,
        private tagService: TagService
    ) { }

    ngOnInit() {
        this.loadTags();
        this.loadUserFavorites();
        this.loadGamesFromDatabase();
    }

    loadTags() {
        // Keep Sidebar Tags Logic
        this.tagService.getTagStats().subscribe({
            next: (response) => {
                this.genres = response.stats.genres.filter(
                    (genre: TagWithCount) => genre.name !== 'Massively Multiplayer' && genre.name !== 'Early Access'
                );
                this.platforms = response.stats.platforms;
                this.playerModes = response.stats.player_modes;

                // If games are already loaded, update counts immediately
                if (this.allGames.length > 0) {
                    this.updateTagCounts();
                }
            },
            error: (err) => console.error('Error loading tags:', err)
        });
    }

    // Sidebar Toggles (Keep functionality)
    toggleSection(section: 'platform' | 'player' | 'genre') {
        this.expandedSections[section] = !this.expandedSections[section];
    }
    toggleGenre(id: number) { this.toggleFilter(this.selectedGenreIds, id); }
    togglePlatform(id: number) { this.toggleFilter(this.selectedPlatformIds, id); }
    togglePlayerMode(id: number) { this.toggleFilter(this.selectedPlayerModeIds, id); }

    private toggleFilter(array: number[], id: number) {
        const index = array.indexOf(id);
        if (index > -1) array.splice(index, 1);
        else array.push(id);

        // Re-apply filters
        this.filterGames();
    }

    isGenreSelected(id: number): boolean { return this.selectedGenreIds.includes(id); }
    isPlatformSelected(id: number): boolean { return this.selectedPlatformIds.includes(id); }
    isPlayerModeSelected(id: number): boolean { return this.selectedPlayerModeIds.includes(id); }

    loadGamesFromDatabase() {
        this.isLoading = true;
        this.error = null;

        // Load ALL games at once (no pagination from backend)
        this.gameService.getGames(0, 2000, []).subscribe({  // Load up to 2000
            next: (gamesFromDb) => {
                console.log('API Response:', gamesFromDb ? gamesFromDb.length : 'null');
                if (gamesFromDb && gamesFromDb.length > 0) {
                    this.allGames = gamesFromDb.map((game: any) => {
                        const genres = game.genre ? game.genre.split(',').map((g: string) => g.trim()) : [];
                        return {
                            id: game.id,
                            title: game.title || 'Unknown Game',
                            description: game.description || game.developer || 'No description available',
                            releaseDate: game.release_date || 'Unknown',
                            genres: genres,
                            reviewTags: [],
                            image: game.image_url || `https://via.placeholder.com/460x215?text=${encodeURIComponent(game.title)}`,
                            reviewType: undefined,
                            isNew: false,
                            platform: game.platform,
                            price: game.price
                        };
                    });

                    // Initial sort
                    this.sortByReleaseDate();

                    // Initial filter (if any tags selected)
                    this.filterGames();

                    this.isLoading = false;
                    this.updateFavoriteStatus();
                    this.loadGameSentiments();
                } else {
                    this.error = 'No games found.';
                    this.isLoading = false;
                    this.loadFallbackGames();
                }
            },
            error: (err: any) => {
                console.error('Error loading games:', err);
                this.error = 'Failed to connect to server';
                this.isLoading = false;
                this.loadFallbackGames();
            }
        });
    }

    loadFallbackGames() {
        this.allGames = [
            {
                id: 1,
                title: 'Apex Legends',
                description: 'เกมผสมผสาน Battle Royale',
                releaseDate: '2019-10-04',
                genres: ['Battle Royale', 'FPS'],
                reviewTags: [],
                image: 'https://cdn.cloudflare.steamstatic.com/steam/apps/1172470/header.jpg',
                reviewType: 'positive',
                isNew: false
            }
        ];
        this.filterGames();
    }

    // Pagination Getters
    get totalPages(): number {
        return Math.ceil(this.games.length / this.gamesPerPage);
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
        for (let i = startPage; i <= endPage; i++) { pages.push(i); }
        return pages;
    }

    goToPage(page: number) {
        if (page >= 1 && page <= this.totalPages) {
            this.currentPage = page;
            this.getPaginatedGames();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }
    previousPage() { this.goToPage(this.currentPage - 1); }
    nextPage() { this.goToPage(this.currentPage + 1); }

    loadGameSentiments() {
        const gameIds = this.games.map(g => g.id); // Only visible games? Or all? 
        // Better to load mostly for visible games, but simpler to load for 'games' (which is filtered set)
        // If games.length is 800, this API call is huge.
        // Let's optimize: Load only for paginatedGames?
        // But user code loaded *batch*.
        // I will load for PAGINATED games inside getPaginatedGames() to be safe.
    }

    loadSentimentsForPage() {
        const gameIds = this.paginatedGames.map(g => g.id);
        if (gameIds.length === 0) return;
        this.gameService.getBatchSentiment(gameIds).subscribe({
            next: (sentiments) => {
                this.paginatedGames.forEach(game => {
                    const sentiment = sentiments[game.id];
                    if (sentiment) {
                        const diff = Math.abs(sentiment.positive_percent - sentiment.negative_percent);
                        if (diff <= 10) game.reviewType = 'mixed';
                        else if (sentiment.positive_percent > sentiment.negative_percent) game.reviewType = 'positive';
                        else game.reviewType = 'negative';
                    }
                });
            }
        });
    }

    // Filter Logic (Client Side)
    filterGames() {
        let filtered = this.allGames;

        // 1. Text Search
        if (this.searchQuery.trim()) {
            const query = this.searchQuery.toLowerCase();
            filtered = filtered.filter(game => game.title.toLowerCase().includes(query));
        }

        // 2. Genre Filter (AND Logic: Game must have ALL selected genres)
        if (this.selectedGenreIds.length > 0) {
            const selectedGenreNames = this.genres
                .filter(g => this.selectedGenreIds.includes(g.id))
                .map(g => g.name);

            if (selectedGenreNames.length > 0) {
                filtered = filtered.filter(game =>
                    selectedGenreNames.every(name => game.genres.includes(name))
                );
            }
        }

        // 3. Platform Filter (OR Logic: Show games on ANY of the selected platforms)
        if (this.selectedPlatformIds.length > 0) {
            const selectedPlatformNames = this.platforms
                .filter(p => this.selectedPlatformIds.includes(p.id))
                .map(p => p.name.toLowerCase());

            if (selectedPlatformNames.length > 0) {
                filtered = filtered.filter(game => {
                    const gamePlatform = (game.platform || '').toLowerCase();
                    return selectedPlatformNames.some(p => gamePlatform.includes(p));
                });
            }
        }

        // 4. Player Mode Filter (Placeholder - requires backend update to map to game object)
        // Currently not available in 'allGames' data.

        this.games = filtered;
        this.updateTagCounts(); // Update counts based on current filters
        this.currentPage = 1;
        this.getPaginatedGames();
    }

    updateTagCounts() {
        // 1. Base Search Filter
        let searchFiltered = this.allGames;
        if (this.searchQuery.trim()) {
            const query = this.searchQuery.toLowerCase();
            searchFiltered = searchFiltered.filter(game => game.title.toLowerCase().includes(query));
        }

        // 2. Prepare Sets for Counting

        // For Genre Counts: Filter by Platform ONLY (ignore current genre selection to show potential count)
        // Actually, users usually expect "Refined Count" (Intersection).
        // But for AND logic filter (Genre), showing "0" for unselected means "If you click this, you get 0 result".
        // This is correct. So we applied platform filter.
        let gamesForGenres = searchFiltered;

        if (this.selectedPlatformIds.length > 0) {
            const selectedPlatformNames = this.platforms
                .filter(p => this.selectedPlatformIds.includes(p.id))
                .map(p => p.name.toLowerCase());

            if (selectedPlatformNames.length > 0) {
                gamesForGenres = gamesForGenres.filter(game => {
                    const gamePlatform = (game.platform || '').toLowerCase();
                    return selectedPlatformNames.some(p => gamePlatform.includes(p));
                });
            }
        }

        // For Platform Counts: Filter by Genre ONLY (ignore current platform selection)
        // Because Platform is OR logic, we usually want to show "How many games match this platform" 
        // within the current Genre/Search scope.
        let gamesForPlatforms = searchFiltered;
        if (this.selectedGenreIds.length > 0) {
            const selectedGenreNames = this.genres
                .filter(g => this.selectedGenreIds.includes(g.id))
                .map(g => g.name);

            if (selectedGenreNames.length > 0) {
                gamesForPlatforms = gamesForPlatforms.filter(game =>
                    selectedGenreNames.every(name => game.genres.includes(name))
                );
            }
        }

        // 3. Update Counts

        // Update Genres
        this.genres.forEach(genre => {
            // Count how many games in the filtered set have this genre
            genre.game_count = gamesForGenres.filter(g => g.genres.includes(genre.name)).length;
        });

        // Update Platforms
        this.platforms.forEach(platform => {
            const pName = platform.name.toLowerCase();
            // Match logic must match filter logic (substring check)
            platform.game_count = gamesForPlatforms.filter(g => (g.platform || '').toLowerCase().includes(pName)).length;
        });
    }

    // Explicit binding trigger
    onSearchChange(newValue: string) {
        console.log('Search Change:', newValue);
        this.searchQuery = newValue;
        this.filterGames();
    }

    sortByReleaseDate() {
        this.games.sort((a, b) => {
            // Handle 'Unknown' or bad dates
            if (a.releaseDate === 'Unknown') return 1;
            if (b.releaseDate === 'Unknown') return -1;
            return new Date(b.releaseDate).getTime() - new Date(a.releaseDate).getTime();
        });
        // Note: this.games is overwritten in filterGames.
        // Sort should happen strictly on filterGames?
        // Or allGames should be sorted.
        this.allGames.sort((a, b) => {
            if (a.releaseDate === 'Unknown') return 1;
            if (b.releaseDate === 'Unknown') return -1;
            return new Date(b.releaseDate).getTime() - new Date(a.releaseDate).getTime();
        });
        this.filterGames();
    }

    getPaginatedGames() {
        const start = (this.currentPage - 1) * this.gamesPerPage;
        const end = start + this.gamesPerPage;
        this.paginatedGames = this.games.slice(start, end);
        this.loadSentimentsForPage(); // Load sentiments for these
        this.updateFavoriteStatus();
    }

    // Favorites Logic
    loadUserFavorites() {
        const user = this.authService.getCurrentUserValue();
        if (!user) return;
        this.favoriteService.getUserFavorites(user.id).subscribe({
            next: (favorites) => {
                this.userFavoriteIds = favorites.map((f: any) => f.id);
                this.updateFavoriteStatus();
            },
            error: (err) => console.error(err)
        });
    }

    updateFavoriteStatus() {
        this.paginatedGames.forEach(game => {
            game.isFavorite = this.userFavoriteIds.includes(game.id);
        });
    }

    toggleFavorite(event: Event, game: Game) {
        event.stopPropagation();
        event.preventDefault();
        const user = this.authService.getCurrentUserValue();
        if (!user) { this.router.navigate(['/login']); return; }

        if (game.isFavorite) {
            this.pendingRemoveGameId = game.id;
            this.pendingRemoveGameTitle = game.title;
            this.showRemoveDialog = true;
        } else {
            // Add logic? Or usually only Remove is guarded?
            // Add is usually instant.
            this.favoriteService.addFavorite(user.id, game.id).subscribe(() => {
                this.userFavoriteIds.push(game.id);
                this.updateFavoriteStatus();
            });
        }
    }

    confirmRemove() {
        const user = this.authService.getCurrentUserValue();
        if (!user || !this.pendingRemoveGameId) return;
        this.favoriteService.removeFavorite(user.id, this.pendingRemoveGameId).subscribe(() => {
            this.userFavoriteIds = this.userFavoriteIds.filter(id => id !== this.pendingRemoveGameId);
            this.updateFavoriteStatus();
            this.showRemoveDialog = false;
            this.pendingRemoveGameId = null;
        });
    }
    cancelRemove() { this.showRemoveDialog = false; this.pendingRemoveGameId = null; }
}
