import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterModule, Router } from '@angular/router';
import { HeaderComponent } from '../../shared/header.component';
import { FooterComponent } from '../../shared/footer.component';
import { TagModule } from 'primeng/tag';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { ProgressBarModule } from 'primeng/progressbar';
import { TextareaModule } from 'primeng/textarea';
import { FormsModule } from '@angular/forms';
import { GameService } from '../../services/game.service';
import { FavoriteService } from '../../services/favorite.service';
import { AuthService } from '../../services/auth.service';
import { CommentService, Comment } from '../../services/comment.service';

interface Review {
    id: number;
    username: string;
    rating: number;
    date: string;
    content: string;
    helpful: number;
}

interface RelatedGame {
    id: number;
    title: string;
    image: string;
    date: string;
    tags: string[];
    reviewTags: string[];
}

@Component({
    selector: 'app-game-detail',
    standalone: true,
    imports: [
        CommonModule,
        HeaderComponent,
        FooterComponent,
        RouterModule,
        TagModule,
        ButtonModule,
        CardModule,
        ProgressBarModule,
        TextareaModule,
        FormsModule
    ],
    templateUrl: './game-detail.component.html',
    styleUrls: ['./game-detail.component.css']
})
export class GameDetailComponent implements OnInit {
    @ViewChild('reviewsContainer') reviewsContainer!: ElementRef;

    gameId: string | null = '';
    isLoading = true;
    error: string | null = null;

    game: any = {
        title: '',
        image: '',
        tags: [],
        releaseDate: '',
        developer: '',
        publisher: '',
        platform: '',
        description: '',
        aboutGameTh: '',
        appId: null,
        score: 0,
        ratings: {
            excellent: 0,
            good: 0,
            average: 0,
            poor: 0
        },
        sentiment: {
            positive: 0,
            negative: 0
        },
        reviewTags: [],
        minRequirements: ''
    };

    // Steam reviews
    steamReviews: any[] = [];
    loadingSteamReviews = false;
    steamReviewsError: string | null = null;

    // Steam sentiment analysis
    loadingSentiment = true;  // Start as true to show loading initially
    sentimentError: string | null = null;
    totalReviewsAnalyzed = 0;

    // Favorites
    isFavorited = false;
    isTogglingFavorite = false;

    // Comments
    comments: Comment[] = [];
    newComment = '';
    isSubmittingComment = false;
    editingCommentId: number | null = null;
    editingContent = '';

    // Mock data for reviews - will be replaced with real data later
    reviews: Review[] = [
        {
            id: 1,
            username: 'User01',
            rating: 5,
            date: '15 ก.ย. 2567',
            content: 'เกมแอ็คชั่นเมคคาที่ดีที่สุดในรอบหลายปี! ระบบการปรับแต่งเมคคาลึกซึ้งมาก การต่อสู้สนุกและท้าทาย กราฟิกสวยงาม เหมาะกับคนที่ชอบเกมแนว Souls-like และเมคคา',
            helpful: 125
        },
        {
            id: 2,
            username: 'User02',
            rating: 4,
            date: '3 ก.ย. 2567',
            content: 'เกมสนุกดี แต่ความยากค่อนข้างสูงสำหรับมือใหม่ ต้องใช้เวลาในการเรียนรู้ระบบการควบคุมและการปรับแต่งเมคคา แต่พอเข้าใจแล้วก็สนุกมาก',
            helpful: 89
        },
        {
            id: 3,
            username: 'Duck',
            rating: 5,
            date: '8 ส.ค. 2567',
            content: 'FromSoftware ทำได้ดีอีกแล้ว! เนื้อเรื่องน่าสนใจ ระบบการต่อสู้ลื่นไหล และมีเนื้อหาให้เล่นเยอะมาก คุ้มค่ากับราคาแน่นอน',
            helpful: 203
        },
        {
            id: 4,
            username: 'Dug',
            rating: 4,
            date: '1 ส.ค. 2567',
            content: 'กราฟิกสวยงาม เสียงเพลงเข้ากับบรรยากาศ แต่บางภารกิจยากเกินไปจนต้องลองหลายรอบ โดยรวมแล้วเป็นเกมที่ดีมาก',
            helpful: 156
        },
        {
            id: 5,
            username: 'GameZ3',
            rating: 5,
            date: '27 ก.ค. 2567',
            content: 'รอมานานและไม่ผิดหวัง! ระบบการปรับแต่งเมคคามีความหลากหลายมาก สามารถสร้างสไตล์การเล่นของตัวเอง Boss fight ท้าทายและสนุกทุกตัว',
            helpful: 178
        }
    ];

    // Mock data for related games - will be replaced with real data later
    relatedGames: RelatedGame[] = [
        {
            id: 101,
            title: 'Lies of P',
            image: 'https://cdn.akamai.steamstatic.com/steam/apps/1627720/header.jpg',
            date: '19 ก.ย. 2566',
            tags: ['แอ็คชั่น', 'RPG'],
            reviewTags: ['ท้าทาย', 'สวยงาม']
        },
        {
            id: 102,
            title: 'DAEMON X MACHINA',
            image: 'https://cdn.akamai.steamstatic.com/steam/apps/1167450/header.jpg',
            date: '13 ก.พ. 2563',
            tags: ['แอ็คชั่น', 'เมคคา'],
            reviewTags: ['สนุก', 'ปรับแต่งได้']
        },
        {
            id: 103,
            title: 'Elden Ring',
            image: 'https://cdn.akamai.steamstatic.com/steam/apps/1245620/header.jpg',
            date: '25 ก.พ. 2565',
            tags: ['แอ็คชั่น', 'RPG'],
            reviewTags: ['ยาก', 'คุ้มค่า']
        },
        {
            id: 104,
            title: 'METAL GEAR RISING: REVENGEANCE',
            image: 'https://cdn.akamai.steamstatic.com/steam/apps/235460/header.jpg',
            date: '9 ม.ค. 2557',
            tags: ['แอ็คชั่น', 'เมคคา'],
            reviewTags: ['มันส์', 'เพลงเพราะ']
        }
    ];

    displayedReviewsCount = 3; // Initially show 3 reviews

    constructor(
        private route: ActivatedRoute,
        private router: Router,
        private gameService: GameService,
        private favoriteService: FavoriteService,
        private authService: AuthService,
        private commentService: CommentService
    ) { }

    ngOnInit() {
        this.gameId = this.route.snapshot.paramMap.get('id');
        if (this.gameId) {
            this.loadGameDetails(parseInt(this.gameId));
            this.loadFavoriteStatus(parseInt(this.gameId));
            this.loadComments();
        }
    }

    loadGameDetails(id: number) {
        this.isLoading = true;
        this.error = null;

        this.gameService.getGame(id).subscribe({
            next: (gameData: any) => {
                // Map API data to game object
                this.game = {
                    title: gameData.title || 'Unknown Game',
                    image: gameData.image_url || 'https://via.placeholder.com/460x215?text=No+Image',
                    tags: gameData.genre ? gameData.genre.split(',').map((g: string) => g.trim()) : [],
                    releaseDate: this.formatDate(gameData.release_date) || 'Unknown',
                    developer: gameData.developer || 'Unknown Developer',
                    publisher: gameData.publisher || 'Unknown Publisher',
                    platform: gameData.platform || 'Unknown Platform',
                    description: gameData.description || 'No description available.',
                    aboutGameTh: gameData.about_game_th || '',
                    appId: gameData.app_id,
                    score: 77, // Mock data - will be calculated from reviews later
                    ratings: {
                        excellent: 77,
                        good: 15,
                        average: 5,
                        poor: 3
                    },
                    sentiment: {
                        positive: 82,
                        neutral: 12,
                        negative: 6
                    },
                    reviewTags: [],  // Will be loaded from API
                    minRequirements: gameData.price || 'N/A'
                };
                this.isLoading = false;

                // Always load Steam reviews for game 727 (or any game)
                this.loadSteamReviews(id);

                // Load sentiment analysis
                this.loadSteamSentiment(id);

                // Load review tags
                this.loadReviewTags(id);
            },
            error: (err) => {
                console.error('Error loading game details:', err);
                this.error = 'ไม่สามารถโหลดข้อมูลเกมได้';
                this.isLoading = false;
            }
        });
    }

    formatDate(dateString: string): string {
        if (!dateString) return 'Unknown';

        try {
            // Parse ISO format date (YYYY-MM-DD) from backend
            const date = new Date(dateString);

            // Check if date is valid
            if (isNaN(date.getTime())) {
                return dateString;
            }

            const thaiMonths = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.',
                'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'];
            const day = date.getDate();
            const month = thaiMonths[date.getMonth()];
            const year = date.getFullYear() + 543; // Convert to Buddhist year
            return `${day} ${month} ${year}`;
        } catch (e) {
            console.error('Error formatting date:', e);
            return dateString;
        }
    }

    getRatingIcon(rating: number): string {
        return rating >= 4 ? 'pi-thumbs-up' : rating >= 3 ? 'pi-minus' : 'pi-thumbs-down';
    }

    getRatingColor(rating: number): string {
        return rating >= 4 ? 'text-green-600' : rating >= 3 ? 'text-yellow-600' : 'text-red-600';
    }

    scrollReviews(direction: 'left' | 'right') {
        const container = this.reviewsContainer.nativeElement;
        const scrollAmount = 400; // Width of one card (384px) plus gap

        if (direction === 'left') {
            container.scrollLeft -= scrollAmount;
        } else {
            container.scrollLeft += scrollAmount;
        }
    }

    loadMoreReviews() {
        this.displayedReviewsCount += 3; // Load 3 more reviews each time
    }

    loadSteamReviews(gameId: number) {
        this.loadingSteamReviews = true;
        this.steamReviewsError = null;

        this.gameService.syncSteamReviews(gameId, 20).subscribe({
            next: (response: any) => {
                if (response.success) {
                    this.steamReviews = response.reviews || [];
                    console.log(`Loaded ${this.steamReviews.length} Steam reviews`);
                }
                this.loadingSteamReviews = false;
            },
            error: (err) => {
                console.error('Error loading Steam reviews:', err);
                this.steamReviewsError = 'ไม่สามารถโหลดรีวิวจาก Steam ได้';
                this.loadingSteamReviews = false;
            }
        });
    }

    formatPlaytime(hours: number): string {
        if (!hours || hours === 0) return 'ไม่มีข้อมูล';
        if (hours < 1) return `${Math.round(hours * 60)} นาที`;
        return `${hours.toFixed(1)} ชั่วโมง`;
    }

    getPositiveTags() {
        return this.game.reviewTags.filter((tag: any) =>
            tag.severity === 'success' || tag.severity === 'info'
        );
    }

    getNegativeTags() {
        return this.game.reviewTags.filter((tag: any) =>
            tag.severity === 'danger' || tag.severity === 'warning'
        );
    }

    loadSteamSentiment(gameId: number) {
        this.loadingSentiment = true;
        this.sentimentError = null;

        this.gameService.getSteamSentiment(gameId).subscribe({
            next: (response: any) => {
                if (response.success) {
                    this.game.sentiment.positive = response.positive_percent;
                    this.game.sentiment.negative = response.negative_percent;
                    this.totalReviewsAnalyzed = response.total_reviews;
                    console.log(`Sentiment: ${response.positive_percent}% positive from ${response.total_reviews} reviews`);
                }
                this.loadingSentiment = false;
            },
            error: (err) => {
                console.error('Error loading sentiment:', err);
                this.sentimentError = 'ไม่สามารถโหลดข้อมูลความรู้สึกได้';
                this.loadingSentiment = false;
            }
        });
    }

    loadReviewTags(gameId: number) {
        this.gameService.getReviewTags(gameId).subscribe({
            next: (response: any) => {
                if (response.success) {
                    // Map API response to reviewTags format
                    const positiveTags = response.positive_tags.map((tag: any) => ({
                        label: tag.tag,
                        count: tag.count,
                        severity: 'success'
                    }));

                    const negativeTags = response.negative_tags.map((tag: any) => ({
                        label: tag.tag,
                        count: tag.count,
                        severity: 'danger'
                    }));

                    this.game.reviewTags = [...positiveTags, ...negativeTags];
                    console.log(`Loaded ${this.game.reviewTags.length} review tags`);
                }
            },
            error: (err) => {
                console.error('Error loading review tags:', err);
                // Keep empty array if error
            }
        });
    }

    loadFavoriteStatus(gameId: number) {
        const user = this.authService.getCurrentUserValue();
        if (!user) {
            this.isFavorited = false;
            return;
        }

        this.favoriteService.isFavorited(user.id, gameId).subscribe({
            next: (response) => {
                this.isFavorited = response.is_favorited;
            },
            error: (err) => {
                console.error('Error checking favorite status:', err);
                this.isFavorited = false;
            }
        });
    }

    toggleFavorite() {
        const user = this.authService.getCurrentUserValue();
        if (!user) {
            alert('กรุณาเข้าสู่ระบบเพื่อเพิ่มเกมในรายการโปรด');
            this.router.navigate(['/login']);
            return;
        }

        if (!this.gameId) return;

        this.isTogglingFavorite = true;
        const gameIdNum = parseInt(this.gameId);

        if (this.isFavorited) {
            // Remove from favorites
            this.favoriteService.removeFavorite(user.id, gameIdNum).subscribe({
                next: (response) => {
                    this.isFavorited = false;
                    this.isTogglingFavorite = false;
                    console.log('Removed from favorites');
                },
                error: (err) => {
                    console.error('Error removing favorite:', err);
                    this.isTogglingFavorite = false;
                    alert('เกิดข้อผิดพลาดในการลบออกจากรายการโปรด');
                }
            });
        } else {
            // Add to favorites
            this.favoriteService.addFavorite(user.id, gameIdNum).subscribe({
                next: (response) => {
                    this.isFavorited = true;
                    this.isTogglingFavorite = false;
                    console.log('Added to favorites');
                },
                error: (err) => {
                    console.error('Error adding favorite:', err);
                    this.isTogglingFavorite = false;
                    alert('เกิดข้อผิดพลาดในการเพิ่มในรายการโปรด');
                }
            });
        }
    }

    // Comment methods
    loadComments() {
        if (!this.gameId) return;

        const user = this.authService.getCurrentUserValue();
        const userId = user ? user.id : undefined;

        this.commentService.getComments(parseInt(this.gameId), userId).subscribe({
            next: (comments) => {
                this.comments = comments;
            },
            error: (err) => {
                console.error('Error loading comments:', err);
            }
        });
    }

    submitComment() {
        const user = this.authService.getCurrentUserValue();
        if (!user) {
            alert('กรุณาเข้าสู่ระบบเพื่อแสดงความคิดเห็น');
            this.router.navigate(['/login']);
            return;
        }

        if (!this.newComment.trim()) {
            alert('กรุณากรอกความคิดเห็น');
            return;
        }

        if (!this.gameId) return;

        this.isSubmittingComment = true;

        this.commentService.addComment(parseInt(this.gameId), user.id, this.newComment).subscribe({
            next: () => {
                this.newComment = '';
                this.isSubmittingComment = false;
                this.loadComments();
            },
            error: (err) => {
                console.error('Error adding comment:', err);
                alert('เกิดข้อผิดพลาดในการแสดงความคิดเห็น');
                this.isSubmittingComment = false;
            }
        });
    }

    startEdit(comment: Comment) {
        this.editingCommentId = comment.id;
        this.editingContent = comment.content;
    }

    cancelEdit() {
        this.editingCommentId = null;
        this.editingContent = '';
    }

    saveEdit() {
        const user = this.authService.getCurrentUserValue();
        if (!user || !this.editingCommentId) return;

        if (!this.editingContent.trim()) {
            alert('กรุณากรอกความคิดเห็น');
            return;
        }

        this.commentService.editComment(this.editingCommentId, user.id, this.editingContent).subscribe({
            next: () => {
                this.editingCommentId = null;
                this.editingContent = '';
                this.loadComments();
            },
            error: (err) => {
                console.error('Error editing comment:', err);
                alert('เกิดข้อผิดพลาดในการแก้ไขความคิดเห็น');
            }
        });
    }

    deleteComment(commentId: number) {
        const user = this.authService.getCurrentUserValue();
        if (!user) return;

        if (confirm('คุณต้องการลบความคิดเห็นนี้หรือไม่?')) {
            this.commentService.deleteComment(commentId, user.id).subscribe({
                next: () => {
                    this.loadComments();
                },
                error: (err) => {
                    console.error('Error deleting comment:', err);
                    alert('เกิดข้อผิดพลาดในการลบความคิดเห็น');
                }
            });
        }
    }

    voteComment(commentId: number, voteType: 'up' | 'down') {
        const user = this.authService.getCurrentUserValue();
        if (!user) {
            alert('กรุณาเข้าสู่ระบบเพื่อโหวต');
            this.router.navigate(['/login']);
            return;
        }

        this.commentService.voteComment(commentId, user.id, voteType).subscribe({
            next: () => {
                this.loadComments();
            },
            error: (err) => {
                console.error('Error voting comment:', err);
                alert('เกิดข้อผิดพลาดในการโหวต');
            }
        });
    }

    reportComment(commentId: number) {
        const user = this.authService.getCurrentUserValue();
        if (!user) {
            alert('กรุณาเข้าสู่ระบบเพื่อรายงาน');
            this.router.navigate(['/login']);
            return;
        }

        const reason = prompt('กรุณาระบุเหตุผลในการรายงานความคิดเห็นนี้:');
        if (!reason || !reason.trim()) {
            return;
        }

        this.commentService.reportComment(commentId, user.id, reason).subscribe({
            next: () => {
                alert('รายงานความคิดเห็นเรียบร้อยแล้ว');
            },
            error: (err) => {
                console.error('Error reporting comment:', err);
                if (err.status === 400) {
                    alert('คุณได้รายงานความคิดเห็นนี้แล้ว');
                } else {
                    alert('เกิดข้อผิดพลาดในการรายงาน');
                }
            }
        });
    }

    isOwnComment(comment: Comment): boolean {
        const user = this.authService.getCurrentUserValue();
        return user ? comment.user_id === user.id : false;
    }

    canDeleteComment(comment: Comment): boolean {
        const user = this.authService.getCurrentUserValue();
        if (!user) return false;
        return comment.user_id === user.id || user.user_role === 'Admin';
    }

    formatCommentDate(dateString: string): string {
        if (!dateString) return '';
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'เมื่อสักครู่';
        if (diffMins < 60) return `${diffMins} นาทีที่แล้ว`;
        if (diffHours < 24) return `${diffHours} ชั่วโมงที่แล้ว`;
        if (diffDays < 7) return `${diffDays} วันที่แล้ว`;

        return date.toLocaleDateString('th-TH');
    }
}
