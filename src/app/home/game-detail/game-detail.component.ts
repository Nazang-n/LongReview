import { Component, OnInit, ViewChild, ElementRef, ViewEncapsulation } from '@angular/core';
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
import { DialogModule } from 'primeng/dialog';
import { CarouselModule } from 'primeng/carousel';
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
        FormsModule,
        FormsModule,
        DialogModule,
        CarouselModule
    ],
    templateUrl: './game-detail.component.html',
    styleUrls: ['./game-detail.component.css']
})
export class GameDetailComponent implements OnInit {
    @ViewChild('reviewsContainer') reviewsContainer!: ElementRef;

    gameId: string | null = '';
    isLoading = true;
    error: string | null = null;

    responsiveOptions = [
        {
            breakpoint: '1024px',
            numVisible: 2,
            numScroll: 1
        },
        {
            breakpoint: '768px',
            numVisible: 2,
            numScroll: 1
        },
        {
            breakpoint: '560px',
            numVisible: 1,
            numScroll: 1
        }
    ];

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
        minRequirements: '',

    };
    // Media gallery properties
    videos: any[] = [];
    screenshots: any[] = [];
    allMedia: any[] = []; // Combined: header image + videos + screenshots
    currentMediaIndex: number = 0;

    steamReviews: any[] = [];
    chunkedReviews: any[][] = [];
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

    // Dialog states
    showDeleteDialog = false;
    showReportDialog = false;
    reportReason = '';
    pendingDeleteCommentId: number | null = null;
    pendingReportCommentId: number | null = null;

    // Alert dialogs
    showLoginDialog = false;
    showErrorDialog = false;
    showSuccessDialog = false;
    errorMessage = '';
    successMessage = '';
    loginMessage = '';
    loginRedirect = false;

    // UI States
    isExpanded = false;

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

    // Similar games
    similarGames: any[] = [];

    displayedReviewsCount = 3; // Initially show 3 reviews

    constructor(
        private route: ActivatedRoute,
        public router: Router,
        private gameService: GameService,
        private favoriteService: FavoriteService,
        private authService: AuthService,
        private commentService: CommentService
    ) { }

    ngOnInit() {
        this.route.paramMap.subscribe(params => {
            this.gameId = params.get('id');
            if (this.gameId) {
                const id = parseInt(this.gameId);

                // Reset states when navigating to a new game
                this.isLoading = true;
                this.error = null;
                this.steamReviews = [];
                this.chunkedReviews = [];
                this.comments = [];
                this.similarGames = [];
                this.newComment = '';
                this.editingCommentId = null;
                this.loadingSentiment = true;
                this.loadingSteamReviews = false;

                // Load all game data
                this.loadGameDetails(id);
                this.loadFavoriteStatus(id);
                this.loadComments();
                this.loadSimilarGames(id);

                // Scroll to top on navigation
                window.scrollTo(0, 0);
            }
        });
    }

    loadSimilarGames(id: number) {
        this.gameService.getSimilarGames(id).subscribe({
            next: (games) => {
                this.similarGames = games;
            },
            error: (err) => {
                console.error('Error loading similar games:', err);
            }
        });
    }

    getGameTags(game: any): string[] {
        if (!game) return [];
        const tagsStr = game.genre_th || game.genre || '';
        return tagsStr.split(',').map((t: string) => t.trim()).filter((t: string) => t.length > 0);
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
                    tags: gameData.genre_th ? gameData.genre_th.split(',').map((g: string) => g.trim()) :
                        (gameData.genre ? gameData.genre.split(',').map((g: string) => g.trim()) : []),
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
                        positive: 0,  // Will be loaded from API
                        neutral: 0,
                        negative: 0   // Will be loaded from API
                    },
                    reviewTags: [],  // Will be loaded from API
                    minRequirements: gameData.price || 'N/A'
                };

                // Parse videos and screenshots JSON
                try {
                    if (gameData.video && gameData.video !== 'null') {
                        this.videos = JSON.parse(gameData.video);
                        console.log('Parsed videos:', this.videos);
                    } else {
                        this.videos = [];
                        console.log('No video data available');
                    }
                } catch (e) {
                    console.error('Error parsing videos:', e);
                    console.error('Video data:', gameData.video);
                    this.videos = [];
                }

                try {
                    if (gameData.screenshots && gameData.screenshots !== 'null') {
                        this.screenshots = JSON.parse(gameData.screenshots);
                        console.log('Parsed screenshots:', this.screenshots);
                    } else {
                        this.screenshots = [];
                        console.log('No screenshot data available');
                    }
                } catch (e) {
                    console.error('Error parsing screenshots:', e);
                    console.error('Screenshot data:', gameData.screenshots);
                    this.screenshots = [];
                }

                console.log(`Loaded ${this.videos.length} videos and ${this.screenshots.length} screenshots`);

                // Build unified media array: header image + videos + screenshots
                this.allMedia = [];

                // 1. Add header image first
                this.allMedia.push({
                    type: 'image',
                    url: gameData.image_url,
                    thumbnail: gameData.image_url
                });

                // 2. Add all videos
                this.videos.forEach(video => {
                    this.allMedia.push({
                        type: 'video',
                        url: video.hls_url || video.url,
                        thumbnail: video.thumbnail,
                        name: video.name
                    });
                });

                // 3. Add all screenshots
                this.screenshots.forEach(screenshot => {
                    this.allMedia.push({
                        name: `Screenshot ${screenshot.id}`,
                        type: 'screenshot',
                        url: screenshot.path_full,
                        thumbnail: screenshot.path_thumbnail
                    });
                });

                console.log(`Total media items: ${this.allMedia.length}`);
                this.currentMediaIndex = 0; // Start with header image

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

        this.gameService.syncSteamReviews(gameId, 100).subscribe({
            next: (response: any) => {
                if (response.success) {
                    this.steamReviews = response.reviews || [];
                    console.log(`Loaded ${this.steamReviews.length} Steam reviews`);

                    // Chunk reviews into groups of 2 for 2-row layout
                    this.chunkedReviews = [];
                    for (let i = 0; i < this.steamReviews.length; i += 2) {
                        this.chunkedReviews.push(this.steamReviews.slice(i, i + 2));
                    }
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

    loadingTags = true;
    isLoadingTags = false; // For refresh button spinner

    loadReviewTags(gameId: number, refresh: boolean = false) {
        if (refresh) {
            this.isLoadingTags = true;
        }
        // Ensure loadingTags is true for initial load (implied) or if we want to show spinner for refresh too
        // For consistent UI, let's keep loadingTags true until data arrives, unless specific refresh UX desired.
        // Actually, let's make loadingTags control the section spinner.

        if (!refresh) this.loadingTags = true;

        this.gameService.getReviewTags(gameId, refresh).subscribe({
            next: (response: any) => {
                this.loadingTags = false;
                if (refresh) this.isLoadingTags = false;

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
                    console.log(`Loaded ${this.game.reviewTags.length} review tags (Refreshed: ${refresh})`);
                }
            },
            error: (err) => {
                console.error('Error loading review tags:', err);
                this.loadingTags = false;
                if (refresh) this.isLoadingTags = false;
                // Keep empty array if error
            }
        });
    }

    refreshTags() {
        if (this.gameId) {
            this.loadReviewTags(parseInt(this.gameId), true);
        }
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
            this.showLogin('กรุณาเข้าสู่ระบบเพื่อเพิ่มเกมในรายการโปรด', true);
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
                    this.showError('เกิดข้อผิดพลาดในการลบออกจากรายการโปรด');
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
                    this.showError('เกิดข้อผิดพลาดในการเพิ่มในรายการโปรด');
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
            this.showLogin('กรุณาเข้าสู่ระบบเพื่อแสดงความคิดเห็น', true);
            return;
        }

        if (!this.newComment.trim()) {
            this.showError('กรุณากรอกความคิดเห็น');
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
                this.showError('เกิดข้อผิดพลาดในการแสดงความคิดเห็น');
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
            this.showError('กรุณากรอกความคิดเห็น');
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
                this.showError('เกิดข้อผิดพลาดในการแก้ไขความคิดเห็น');
            }
        });
    }

    deleteComment(commentId: number) {
        this.pendingDeleteCommentId = commentId;
        this.showDeleteDialog = true;
    }

    confirmDelete() {
        const user = this.authService.getCurrentUserValue();
        if (!user || !this.pendingDeleteCommentId) return;

        this.commentService.deleteComment(this.pendingDeleteCommentId, user.id).subscribe({
            next: () => {
                this.loadComments();
                this.showDeleteDialog = false;
                this.pendingDeleteCommentId = null;
            },
            error: (err) => {
                console.error('Error deleting comment:', err);
                this.showError('เกิดข้อผิดพลาดในการลบความคิดเห็น');
                this.showDeleteDialog = false;
            }
        });
    }

    cancelDelete() {
        this.showDeleteDialog = false;
        this.pendingDeleteCommentId = null;
    }

    voteComment(commentId: number, voteType: 'up' | 'down') {
        const user = this.authService.getCurrentUserValue();
        if (!user) {
            this.showLogin('กรุณาเข้าสู่ระบบเพื่อโหวต', true);
            return;
        }

        // Only handle 'up' votes now (like button)
        if (voteType === 'up') {
            this.commentService.likeComment(commentId, user.id).subscribe({
                next: () => {
                    this.loadComments();
                },
                error: (err) => {
                    console.error('Error liking comment:', err);
                    this.showError('เกิดข้อผิดพลาดในการถูกใจ');
                }
            });
        }
    }

    reportComment(commentId: number) {
        const user = this.authService.getCurrentUserValue();
        if (!user) {
            this.showLogin('กรุณาเข้าสู่ระบบเพื่อรายงาน', true);
            return;
        }

        this.pendingReportCommentId = commentId;
        this.reportReason = '';
        this.showReportDialog = true;
    }

    confirmReport() {
        const user = this.authService.getCurrentUserValue();
        if (!user || !this.pendingReportCommentId) return;

        if (!this.reportReason.trim()) {
            this.showError('กรุณาระบุเหตุผลในการรายงาน');
            return;
        }

        this.commentService.reportComment(this.pendingReportCommentId, user.id, this.reportReason).subscribe({
            next: () => {
                this.showSuccess('รายงานความคิดเห็นเรียบร้อยแล้ว');
                this.showReportDialog = false;
                this.pendingReportCommentId = null;
                this.reportReason = '';
            },
            error: (err) => {
                console.error('Error reporting comment:', err);
                if (err.status === 400) {
                    this.showError('คุณได้รายงานความคิดเห็นนี้ไปแล้ว');
                } else {
                    this.showError('เกิดข้อผิดพลาดในการรายงาน');
                }
                this.showReportDialog = false;
            }
        });
    }

    cancelReport() {
        this.showReportDialog = false;
        this.pendingReportCommentId = null;
        this.reportReason = '';
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

    // Helper methods for dialogs
    showLogin(message: string, redirect: boolean = false) {
        this.loginMessage = message;
        this.loginRedirect = redirect;
        this.showLoginDialog = true;
    }

    closeLoginDialog() {
        this.showLoginDialog = false;
        if (this.loginRedirect) {
            this.router.navigate(['/login']);
        }
    }

    showError(message: string) {
        this.errorMessage = message;
        this.showErrorDialog = true;
    }

    closeErrorDialog() {
        this.showErrorDialog = false;
    }

    showSuccess(message: string) {
        this.successMessage = message;
        this.showSuccessDialog = true;
    }

    closeSuccessDialog() {
        this.showSuccessDialog = false;
    }

    // Media navigation methods
    previousMedia() {
        if (this.currentMediaIndex > 0) {
            this.currentMediaIndex--;
        } else {
            this.currentMediaIndex = this.allMedia.length - 1; // Loop to end
        }
    }

    nextMedia() {
        if (this.currentMediaIndex < this.allMedia.length - 1) {
            this.currentMediaIndex++;
        } else {
            this.currentMediaIndex = 0; // Loop to start
        }
    }

    selectMediaByIndex(index: number) {
        this.currentMediaIndex = index;
    }

    getCurrentMedia() {
        return this.allMedia[this.currentMediaIndex];
    }
}
