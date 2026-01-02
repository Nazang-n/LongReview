import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { HeaderComponent } from '../../shared/header.component';
import { FooterComponent } from '../../shared/footer.component';
import { FavoriteService } from '../../services/favorite.service';
import { AuthService } from '../../services/auth.service';
import { DialogModule } from 'primeng/dialog';

interface Game {
    id: number;
    title: string;
    description: string;
    releaseDate: string;
    genres: string[];
    reviewTags: string[];
    image: string;
    reviewType: 'positive' | 'negative' | 'mixed';
    isNew?: boolean;
}

@Component({
    selector: 'app-favorites',
    standalone: true,
    imports: [CommonModule, RouterModule, HeaderComponent, FooterComponent, DialogModule],
    templateUrl: './favorites.component.html',
    styleUrls: ['./favorites.component.css']
})
export class FavoritesComponent implements OnInit {
    favoriteGames: Game[] = [];
    isLoading = true;
    error: string | null = null;

    // Dialog state
    showRemoveDialog = false;
    pendingRemoveGameId: number | null = null;
    pendingRemoveGameTitle: string = '';

    constructor(
        private favoriteService: FavoriteService,
        private authService: AuthService,
        private router: Router
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
                // Map API response to Game interface
                this.favoriteGames = favorites.map((fav: any) => ({
                    id: fav.id,
                    title: fav.title || 'Unknown Game',
                    description: fav.description || fav.info || 'No description available',
                    releaseDate: this.formatDate(fav.release_date) || 'Unknown',
                    genres: fav.genre ? fav.genre.split(',').map((g: string) => g.trim()) : [],
                    reviewTags: [], // Can be populated if needed
                    image: fav.image_url || fav.picture || 'https://via.placeholder.com/460x215?text=No+Image',
                    reviewType: 'positive', // Default, can be calculated from sentiment
                    isNew: false
                }));
                this.isLoading = false;
            },
            error: (err) => {
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
}
