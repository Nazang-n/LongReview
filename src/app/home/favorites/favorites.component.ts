import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { HeaderComponent } from '../../shared/header.component';
import { FooterComponent } from '../../shared/footer.component';
import { FavoriteService } from '../../services/favorite.service';
import { AuthService } from '../../services/auth.service';
import { GameService } from '../../services/game.service';
import { DialogModule } from 'primeng/dialog';

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
}

@Component({
    selector: 'app-favorites',
    standalone: true,
    imports: [CommonModule, RouterModule, HeaderComponent, FooterComponent, DialogModule, FormsModule],
    templateUrl: './favorites.component.html',
    styleUrls: ['./favorites.component.css']
})
export class FavoritesComponent implements OnInit {
    allFavorites: Game[] = [];  // Store all favorites
    favoriteGames: Game[] = [];  // Filtered favorites (after search)
    isLoading = true;
    error: string | null = null;
    searchQuery: string = '';  // Search input

    // Dialog state
    showRemoveDialog = false;
    pendingRemoveGameId: number | null = null;
    pendingRemoveGameTitle: string = '';

    constructor(
        private favoriteService: FavoriteService,
        private authService: AuthService,
        private router: Router,
        private gameService: GameService
    ) { }

    ngOnInit() {
        this.loadFavorites();
    }

    loadFavorites() {
        const user = this.authService.getCurrentUserValue();
        if (!user) {
            this.isLoading = false;
            this.error = 'กรุณาเข้าสู่ระบบเพื่อดูรายการโปรด';
            this.router.navigate(['/login']);
            return;
        }

        this.isLoading = true;
        this.error = null;

        this.favoriteService.getUserFavorites(user.id).subscribe({
            next: (favorites) => {
                // Map API response to Game interface and store in allFavorites
                this.allFavorites = favorites.map((fav: any) => ({
                    id: fav.id,
                    title: fav.title || 'Unknown Game',
                    description: fav.description || fav.info || 'No description available',
                    releaseDate: this.formatDate(fav.release_date) || 'Unknown',
                    genres: fav.genre ? fav.genre.split(',').map((g: string) => g.trim()) : [],
                    reviewTags: [], // Can be populated if needed
                    image: fav.image_url || fav.picture || 'https://via.placeholder.com/460x215?text=No+Image',
                    reviewType: undefined,  // Will be set by loadFavoriteSentiments()
                    isNew: false
                }));

                // Initially show all favorites
                this.favoriteGames = [...this.allFavorites];
                this.isLoading = false;

                // Load sentiment data for review badges
                this.loadFavoriteSentiments();
            },
            error: (err: any) => {
                console.error('Error loading favorites:', err);
                this.error = 'ไม่สามารถโหลดรายการโปรดได้';
                this.isLoading = false;
            }
        });
    }

    formatDate(dateString: string): string {
        if (!dateString) return 'Unknown';

        try {
            const date = new Date(dateString);
            if (isNaN(date.getTime())) {
                return dateString;
            }

            const thaiMonths = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.',
                'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'];
            const day = date.getDate();
            const month = thaiMonths[date.getMonth()];
            const year = date.getFullYear() + 543;
            return `${day} ${month} ${year}`;
        } catch (e) {
            console.error('Error formatting date:', e);
            return dateString;
        }
    }

    removeFavorite(event: Event, gameId: number, gameTitle: string) {
        event.stopPropagation();
        event.preventDefault();

        this.pendingRemoveGameId = gameId;
        this.pendingRemoveGameTitle = gameTitle;
        this.showRemoveDialog = true;
    }

    confirmRemove() {
        const user = this.authService.getCurrentUserValue();
        if (!user || !this.pendingRemoveGameId) return;

        this.favoriteService.removeFavorite(user.id, this.pendingRemoveGameId).subscribe({
            next: () => {
                // Remove from local array
                this.favoriteGames = this.favoriteGames.filter(game => game.id !== this.pendingRemoveGameId);
                this.showRemoveDialog = false;
                this.pendingRemoveGameId = null;
                this.pendingRemoveGameTitle = '';
            },
            error: (err) => {
                console.error('Error removing favorite:', err);
                alert('เกิดข้อผิดพลาดในการลบออกจากรายการโปรด');
                this.showRemoveDialog = false;
            }
        });
    }

    cancelRemove() {
        this.showRemoveDialog = false;
        this.pendingRemoveGameId = null;
        this.pendingRemoveGameTitle = '';
    }

    loadFavoriteSentiments() {
        const gameIds = this.favoriteGames.map(g => g.id);

        if (gameIds.length === 0) return;

        this.gameService.getBatchSentiment(gameIds).subscribe({
            next: (sentiments) => {
                this.favoriteGames.forEach(game => {
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
            // No search query - show all favorites
            this.favoriteGames = [...this.allFavorites];
            return;
        }

        // Filter favorites by title (case-insensitive, partial match)
        const query = this.searchQuery.toLowerCase();
        this.favoriteGames = this.allFavorites.filter(game =>
            game.title.toLowerCase().includes(query)
        );
    }
}
