import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { HeaderComponent } from '../shared/header.component';
import { FooterComponent } from '../shared/footer.component';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { MessageModule } from 'primeng/message';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { NewsService } from '../services/news.service';
import { GameService } from '../services/game.service';
import { CommentService, CommentReport } from '../services/comment.service';
import { AuthService } from '../services/auth.service';
import { DialogModule } from 'primeng/dialog';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';
import { TabViewModule } from 'primeng/tabview';
import { DropdownModule } from 'primeng/dropdown';
import { InputNumberModule } from 'primeng/inputnumber';
import { TableModule } from 'primeng/table';
import { OverlayPanelModule } from 'primeng/overlaypanel';
import { TooltipModule } from 'primeng/tooltip';
import { AnalyticsService, DailyUpdateStatus, IncompleteGame } from '../services/analytics.service';

@Component({
    selector: 'app-admin',
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        HeaderComponent,
        FooterComponent,
        ButtonModule,
        CardModule,
        MessageModule,
        ProgressSpinnerModule,
        DialogModule,
        ToastModule,
        TabViewModule,
        DropdownModule,
        InputNumberModule,
        TableModule,
        OverlayPanelModule,
        TooltipModule
    ],
    providers: [MessageService],
    templateUrl: './admin.component.html',
    styleUrls: ['./admin.component.css']
})
export class AdminComponent implements OnInit, OnDestroy {
    isLoading = false;
    syncResult: any = null;
    error: string | null = null;

    // Translation
    isTranslating = false;
    translateResult: any = null;
    translateError: string | null = null;

    // Comment reports
    reportedComments: CommentReport[] = [];
    isLoadingReports = false;
    reportsError: string | null = null;

    // Dialog states
    showDismissDialog = false;
    showDeleteCommentDialog = false;
    displayResultDialog = false;
    resultDialogTitle = '';
    resultDialogData: any = null;

    pendingReportId: number | null = null;
    pendingCommentId: number | null = null;

    showResultDialog(title: string, data: any) {
        this.resultDialogTitle = title;
        this.resultDialogData = data;
        this.displayResultDialog = true;
    }

    // Review scheduler
    isUpdatingReviews = false;
    reviewUpdateResult: any = null;
    reviewUpdateError: string | null = null;

    // Sentiment cache
    isUpdatingSentiment = false;
    sentimentUpdateResult: any = null;
    sentimentUpdateError: string | null = null;

    // Review tags
    isUpdatingReviewTags = false;
    reviewTagsUpdateResult: any = null;
    reviewTagsUpdateError: string | null = null;
    selectedGameForTagsId: number | null = null;
    isGeneratingTags = false;

    // Untagged Games Dialog
    showUntaggedDialog = false;
    untaggedGames: any[] = [];
    isCheckingUntagged = false;
    showAllIncompleteDialog: boolean = false;
    isGeneratingSingleTag: { [key: number]: boolean } = {};

    // Game import
    selectedImportMethod: string = 'by_id';
    gameAppId: number | null = null;
    batchSize: number = 50;
    isImportingGame = false;

    importMethods = [
        { label: 'เพิ่มเกมด้วย Game ID', value: 'by_id' },
        { label: 'เพิ่มเกมใหม่ล่าสุด', value: 'newest' },
        { label: 'เพิ่มเกมแบบ Batch', value: 'batch' }
    ];

    // Game deletion
    games: any[] = [];
    selectedGameId: number | null = null;
    isDeletingGame = false;
    showDeleteGameDialog = false;

    // Dashboard analytics
    isLoadingAnalytics = false;
    analyticsError: string | null = null;

    // Statistics
    todayComments = 0;
    monthlyComments = 0;
    todayNews = 0;
    todayReports = 0;
    totalPendingReports = 0;

    // Global processing flag to prevent concurrent operations
    isAnyProcessing = false;

    // Auto-refresh interval for dashboard
    private dashboardRefreshInterval: any;

    // Polling intervals
    private pollingIntervals: Map<string, any> = new Map();

    // Daily system updates
    isLoadingDailyUpdates = false;
    newGamesToday = 0;
    dailyUpdates: {
        news: DailyUpdateStatus;
        games: DailyUpdateStatus;
        sentiment: DailyUpdateStatus;
        tags: DailyUpdateStatus;
        reviews: DailyUpdateStatus;
    } | null = null;
    incompleteGames: IncompleteGame[] = [];
    totalNotUpdatedGames = 0;
    isFixingAll = false;

    constructor(
        private newsService: NewsService,
        private gameService: GameService,
        private commentService: CommentService,
        private authService: AuthService,
        private messageService: MessageService,
        private analyticsService: AnalyticsService,
        private http: HttpClient
    ) { }

    ngOnInit() {
        this.loadReportedComments();
        this.loadDashboardAnalytics();
        this.loadDailyUpdateStatus();
        this.loadGames();
    }

    ngOnDestroy() {
        // Clear auto-refresh interval
        if (this.dashboardRefreshInterval) {
            clearInterval(this.dashboardRefreshInterval);
        }
    }

    // Check if any operation is currently processing
    private checkIfProcessing(): boolean {
        if (this.isAnyProcessing) {
            this.messageService.add({
                severity: 'warn',
                summary: 'กรุณารอสักครู่',
                detail: 'กรุณารอการประมวลผลอื่นให้สำเร็จก่อน',
                life: 3000
            });
            return true;
        }
        return false;
    }

    syncNews() {
        if (this.checkIfProcessing()) return;

        this.isAnyProcessing = true;
        this.isLoading = true;
        this.syncResult = null;
        this.error = null;

        this.messageService.add({
            severity: 'info',
            summary: 'ซิงค์ข่าวสารเริ่มต้น',
            detail: 'กำลังดึงข่าวล่าสุดจาก API คุณจะได้รับการแจ้งเตือนเมื่อเสร็จสิ้น',
            life: 3000
        });

        this.newsService.syncNews().subscribe({
            next: (result) => {
                this.isLoading = false;
                this.isAnyProcessing = false;
                this.showResultDialog('ซิงค์ข่าวสารสำเร็จ', {
                    'เพิ่มใหม่': result.added || 0,
                    'อัปเดต': result.updated || 0,
                    'ทั้งหมด': result.total_processed || 0
                });
            },
            error: (err) => {
                this.isLoading = false;
                this.isAnyProcessing = false;
                this.messageService.add({ severity: 'error', summary: 'เกิดข้อผิดพลาด', detail: err.message || 'ไม่สามารถซิงค์ข่าวได้' });
            }
        });
    }

    translateGames() {
        if (this.checkIfProcessing()) return;

        this.isAnyProcessing = true;
        this.isTranslating = true;
        this.translateResult = null;
        this.translateError = null;

        this.messageService.add({
            severity: 'info',
            summary: 'การแปลภาษาเริ่มต้น',
            detail: 'กำลังแปลข้อมูลเกมเป็นภาษาไทย คุณจะได้รับการแจ้งเตือนเมื่อเสร็จสิ้น',
            life: 3000
        });

        this.gameService.batchTranslateGames().subscribe({
            next: (result: any) => {
                this.isTranslating = false;
                this.isAnyProcessing = false;
                this.showResultDialog('การแปลภาษาเสร็จสิ้น', {
                    'แปลแล้ว': result.translated || 0,
                    'ล้มเหลว': result.failed || 0
                });
            },
            error: (err: any) => {
                this.isTranslating = false;
                this.isAnyProcessing = false;
                this.messageService.add({ severity: 'error', summary: 'เกิดข้อผิดพลาด', detail: err.message || 'ไม่สามารถแปลเกมได้' });
            }
        });
    }

    // Comment moderation methods
    loadReportedComments() {
        const user = this.authService.getCurrentUserValue();
        if (!user || user.user_role !== 'Admin') {
            return;
        }

        this.isLoadingReports = true;
        this.reportsError = null;

        this.commentService.getAllReports(user.id).subscribe({
            next: (reports) => {
                this.reportedComments = reports;
                this.totalPendingReports = reports.length;
                this.isLoadingReports = false;
            },
            error: (err) => {
                console.error('Error loading reports:', err);
                this.reportsError = 'ไม่สามารถโหลดรายงานได้';
                this.isLoadingReports = false;
            }
        });
    }

    dismissReport(reportId: number) {
        this.pendingReportId = reportId;
        this.showDismissDialog = true;
    }

    confirmDismissReport() {
        const user = this.authService.getCurrentUserValue();
        if (!user || !this.pendingReportId) return;

        this.commentService.dismissReport(this.pendingReportId, user.id).subscribe({
            next: () => {
                this.loadReportedComments();
                this.loadDashboardAnalytics(); // Refresh dashboard pending reports count
                this.showDismissDialog = false;
                this.pendingReportId = null;
            },
            error: (err) => {
                console.error('Error dismissing report:', err);
                alert('เกิดข้อผิดพลาดในการยกเลิกรายงาน');
                this.showDismissDialog = false;
            }
        });
    }

    cancelDismissReport() {
        this.showDismissDialog = false;
        this.pendingReportId = null;
    }

    deleteReportedComment(commentId: number) {
        this.pendingCommentId = commentId;
        this.showDeleteCommentDialog = true;
    }

    confirmDeleteComment() {
        const user = this.authService.getCurrentUserValue();
        if (!user || !this.pendingCommentId) return;

        this.commentService.deleteComment(this.pendingCommentId, user.id).subscribe({
            next: () => {
                this.loadReportedComments();
                this.loadDashboardAnalytics(); // Refresh dashboard pending reports count
                this.showDeleteCommentDialog = false;
                this.pendingCommentId = null;
            },
            error: (err) => {
                console.error('Error deleting comment:', err);
                alert('เกิดข้อผิดพลาดในการลบความคิดเห็น');
                this.showDeleteCommentDialog = false;
            }
        });
    }

    cancelDeleteComment() {
        this.showDeleteCommentDialog = false;
        this.pendingCommentId = null;
    }

    triggerReviewUpdate() {
        if (this.checkIfProcessing()) return;

        this.isAnyProcessing = true;
        this.isUpdatingReviews = true;
        this.reviewUpdateResult = null;
        this.reviewUpdateError = null;

        this.messageService.add({
            severity: 'info',
            summary: 'อัปเดตรีวิวภาษาไทยเริ่มต้น',
            detail: 'กำลังดึงรีวิวภาษาไทย คุณจะได้รับการแจ้งเตือนเมื่อเสร็จสิ้น',
            life: 3000
        });

        this.gameService.triggerReviewUpdate().subscribe({
            next: (result) => {
                this.reviewUpdateResult = result;
                this.isUpdatingReviews = false;
                this.isAnyProcessing = false;

                // Build detailed message from stats
                const stats = result.stats || {};

                // Show result dialog
                this.showResultDialog('อัปเดตรีวิวภาษาไทยสำเร็จ', {
                    'เกมที่ประมวลผล': stats.games_processed || 0,
                    'สำเร็จ': stats.games_successful || 0,
                    'ล้มเหลว': stats.games_failed || 0,
                    'รีวิวใหม่': stats.new_reviews_fetched || 0
                });
            },
            error: (err) => {
                this.reviewUpdateError = err.message || 'Failed to trigger review update';
                this.isUpdatingReviews = false;
                this.isAnyProcessing = false;

                // Show error toast
                this.messageService.add({
                    severity: 'error',
                    summary: 'อัปเดตล้มเหลว',
                    detail: this.reviewUpdateError || undefined,
                    life: 5000
                });
            }
        });
    }

    triggerSentimentUpdate() {
        if (this.checkIfProcessing()) return;

        this.isAnyProcessing = true;
        this.isUpdatingSentiment = true;
        this.sentimentUpdateResult = null;
        this.sentimentUpdateError = null;

        this.messageService.add({
            severity: 'info',
            summary: 'อัปเดต Sentiment เริ่มต้น',
            detail: 'กำลังอัปเดต Sentiment ของเกม คุณจะได้รับการแจ้งเตือนเมื่อเสร็จสิ้น',
            life: 3000
        });

        this.gameService.triggerSentimentUpdate().subscribe({
            next: (result: any) => {
                this.sentimentUpdateResult = result;
                this.isUpdatingSentiment = false;
                this.isAnyProcessing = false;

                // Backend now runs synchronously, show completion results
                const stats = result.stats || {};

                // Show result dialog with statistics
                this.showResultDialog('อัปเดต Sentiment สำเร็จ', {
                    'เกมที่ประมวลผล': stats.games_processed || 0,
                    'อัปเดต': stats.updated || 0,
                    'ข้อผิดพลาด': stats.errors || 0
                });
            },
            error: (err: any) => {
                this.sentimentUpdateError = err.message || 'Failed to trigger sentiment update';
                this.isUpdatingSentiment = false;
                this.isAnyProcessing = false;

                // Show error toast
                this.messageService.add({
                    severity: 'error',
                    summary: 'อัปเดตล้มเหลว',
                    detail: this.sentimentUpdateError || undefined,
                    life: 5000
                });
            }
        });
    }

    triggerReviewTagsUpdate() {
        if (this.checkIfProcessing()) return;

        this.isAnyProcessing = true;
        this.isUpdatingReviewTags = true;
        this.reviewTagsUpdateResult = null;
        this.reviewTagsUpdateError = null;

        this.messageService.add({
            severity: 'info',
            summary: 'อัปเดต Review Tags เริ่มต้น',
            detail: 'กำลังสร้าง Review Tags คุณจะได้รับการแจ้งเตือนเมื่อเสร็จสิ้น',
            life: 3000
        });

        this.gameService.triggerReviewTagsUpdate().subscribe({
            next: (result: any) => {
                this.reviewTagsUpdateResult = result;
                this.isUpdatingReviewTags = false;
                this.isAnyProcessing = false;

                // Build detailed message from stats
                const stats = result.stats || {};

                // Show result dialog
                this.showResultDialog('อัปเดต Review Tags สำเร็จ', {
                    'เกมที่ตรวจสอบ': stats.games_checked || 0,
                    'อัปเดต': stats.updated || 0,
                    'ข้าม': stats.skipped || 0,
                    'ข้อผิดพลาด': stats.errors || 0
                });
            },
            error: (err: any) => {
                this.reviewTagsUpdateError = err.message || 'Failed to trigger review tags update';
                this.isUpdatingReviewTags = false;
                this.isAnyProcessing = false;

                // Show error toast
                this.messageService.add({
                    severity: 'error',
                    summary: 'อัปเดตล้มเหลว',
                    detail: this.reviewTagsUpdateError || undefined,
                    life: 5000
                });
            }
        });
    }

    generateTagsForGame() {
        if (!this.selectedGameForTagsId) {
            this.messageService.add({
                severity: 'warn',
                summary: 'กรุณาเลือกเกม',
                detail: 'กรุณาเลือกเกมที่ต้องการสร้างแท็ก',
                life: 3000
            });
            return;
        }

        if (this.checkIfProcessing()) return;

        this.isAnyProcessing = true;
        this.isGeneratingTags = true;

        this.messageService.add({
            severity: 'info',
            summary: 'กำลังสร้างแท็ก',
            detail: 'กำลังวิเคราะห์รีวิวและสร้างแท็ก...',
            life: 3000
        });

        this.gameService.generateTagsForGame(this.selectedGameForTagsId).subscribe({
            next: (result: any) => {
                this.isGeneratingTags = false;
                this.isAnyProcessing = false;

                const data = result.data || {};
                const posCount = data.positive_tags ? data.positive_tags.length : 0;
                const negCount = data.negative_tags ? data.negative_tags.length : 0;

                // Find game name from local list if not in response
                let gameName = data.game_name;
                if (!gameName && this.selectedGameForTagsId) {
                    const selectedGame = this.games.find(g => g.id === this.selectedGameForTagsId);
                    if (selectedGame) {
                        gameName = selectedGame.title;
                    }
                }

                this.showResultDialog('สร้างแท็กสำเร็จ', {
                    'เกม': gameName || 'ไม่ระบุ',
                    'แท็กแง่บวก': posCount,
                    'แท็กแง่ลบ': negCount,
                    'รีวิวที่วิเคราะห์': data.total_reviews_analyzed || 0
                });

                this.selectedGameForTagsId = null;
            },
            error: (err: any) => {
                this.isGeneratingTags = false;
                this.isAnyProcessing = false;

                this.messageService.add({
                    severity: 'error',
                    summary: 'เกิดข้อผิดพลาด',
                    detail: err.error?.detail || err.message || 'ไม่สามารถสร้างแท็กได้',
                    life: 5000
                });
            }
        });
    }

    importGame() {
        if (this.checkIfProcessing()) return;

        // Validate inputs based on selected method
        if (this.selectedImportMethod === 'by_id') {
            if (!this.gameAppId) {
                this.messageService.add({
                    severity: 'warn',
                    summary: 'กรุณากรอกข้อมูล',
                    detail: 'กรุณากรอก Steam App ID',
                    life: 3000
                });
                return;
            }
        } else {
            if (!this.batchSize || this.batchSize <= 0) {
                this.messageService.add({
                    severity: 'warn',
                    summary: 'กรุณากรอกข้อมูล',
                    detail: 'กรุณากรอกจำนวนเกมที่ต้องการเพิ่ม',
                    life: 3000
                });
                return;
            }
        }

        this.isImportingGame = true;
        this.isAnyProcessing = true;

        this.messageService.add({
            severity: 'info',
            summary: 'เริ่มนำเข้าเกม',
            detail: 'กำลังดำเนินการนำเข้าเกม...',
            life: 3000
        });

        let importObservable;

        switch (this.selectedImportMethod) {
            case 'by_id':
                importObservable = this.gameService.importGameById(this.gameAppId!);
                break;
            case 'newest':
                importObservable = this.gameService.importNewestGames(this.batchSize);
                break;
            case 'batch':
                importObservable = this.gameService.importGamesFromSteamSpy(this.batchSize);
                break;
            default:
                this.isImportingGame = false;
                return;
        }

        importObservable.subscribe({
            next: (result: any) => {
                this.isImportingGame = false;
                this.isAnyProcessing = false;

                // Debug: Log the full response to see structure
                console.log('Import game response:', result);

                // Build result data for dialog
                if (this.selectedImportMethod === 'by_id') {
                    // Single game import - try different possible response structures
                    const gameTitle = result.game?.title || result.game?.name || result.title || result.name || 'ไม่ทราบชื่อเกม';

                    // Debug: Log what we found
                    console.log('Game title found:', gameTitle);
                    console.log('result.game:', result.game);

                    this.showResultDialog('นำเข้าเกมสำเร็จ', {
                        'ชื่อเกม': gameTitle
                    });
                } else {
                    // Batch import
                    const stats = result.stats || result;
                    this.showResultDialog('นำเข้าเกมสำเร็จ', {
                        'เพิ่มแล้ว': stats.added || stats.imported || 0,
                        'อัปเดต': stats.updated || 0,
                        'ล้มเหลว': stats.failed || stats.errors || 0
                    });
                }

                // Reset form
                if (this.selectedImportMethod === 'by_id') {
                    this.gameAppId = null;
                }
            },
            error: (err: any) => {
                this.isImportingGame = false;
                this.isAnyProcessing = false;

                this.messageService.add({
                    severity: 'error',
                    summary: 'นำเข้าเกมล้มเหลว',
                    detail: err.error?.detail || err.message || 'เกิดข้อผิดพลาดในการนำเข้าเกม',
                    life: 5000
                });
            }
        });
    }

    loadDashboardAnalytics() {
        this.isLoadingAnalytics = true;
        this.analyticsError = null;

        // Load all analytics data concurrently
        Promise.all([
            this.analyticsService.getCommentAnalytics().toPromise(),
            this.analyticsService.getNewsAnalytics().toPromise(),
            this.analyticsService.getReportAnalytics().toPromise()
        ]).then(([comments, news, reports]) => {
            // Update comment data
            this.todayComments = comments?.today_count || 0;
            this.monthlyComments = comments?.monthly_total || 0;

            // Update news data
            this.todayNews = news?.today_count || 0;

            // Update reports data
            this.todayReports = reports?.today_count || 0;
            this.totalPendingReports = reports?.total_pending || this.reportedComments.length;

            this.isLoadingAnalytics = false;
        }).catch(error => {
            console.error('Error loading analytics:', error);
            this.analyticsError = 'ไม่สามารถโหลดข้อมูลสถิติได้';
            this.isLoadingAnalytics = false;
        });
    }

    loadGames() {
        this.gameService.getGamesList().subscribe({
            next: (response: any) => {
                this.games = response.games || [];
            },
            error: (err: any) => {
                console.error('Error loading games:', err);
                this.messageService.add({
                    severity: 'error',
                    summary: 'เกิดข้อผิดพลาด',
                    detail: 'ไม่สามารถโหลดรายชื่อเกมได้'
                });
            }
        });
    }

    loadDailyUpdateStatus() {
        this.isLoadingDailyUpdates = true;

        Promise.all([
            this.analyticsService.getNewGamesToday().toPromise(),
            this.analyticsService.getDailyUpdates().toPromise(),
            this.analyticsService.getIncompleteGames().toPromise(),
        ]).then(([newGames, dailyUpdates, incompleteGamesData]) => {
            // Update new games count
            this.newGamesToday = newGames?.new_games_count || 0;

            // Update daily updates status
            this.dailyUpdates = dailyUpdates?.updates || null;

            if (incompleteGamesData) {
                this.incompleteGames = incompleteGamesData.games;
                this.totalNotUpdatedGames = incompleteGamesData.total_not_updated;
            }
            this.isLoadingDailyUpdates = false;
        }).catch(error => {
            console.error('Error loading daily update status:', error);
            this.isLoadingDailyUpdates = false;
        });
    }

    getStatusIcon(status: DailyUpdateStatus): string {
        // Only 2 states: updated or not updated
        return status.fetched ? 'pi-check-circle' : 'pi-minus-circle';
    }

    getStatusColor(status: DailyUpdateStatus): string {
        // Only 2 colors: green (updated) or gray (not updated)
        return status.fetched ? 'text-green-600' : 'text-gray-400';
    }

    getNotUpdatedLabel(dataType: string): string {
        const labels: { [key: string]: string } = {
            'sentiment': 'เปอร์เซ็นต์รีวิว',
            'tags': 'แท็กรีวิว',
            'reviews': 'รีวิวภาษาไทย'
        };
        return labels[dataType] || dataType;
    }

    fixIncompleteGame(game: IncompleteGame) {
        if (this.checkIfProcessing()) return;

        this.isAnyProcessing = true;

        this.messageService.add({
            severity: 'info',
            summary: 'กำลังอัปเดตข้อมูล',
            detail: `กำลังอัปเดตข้อมูลสำหรับ ${game.title}...`,
            life: 3000
        });

        const updates: any[] = [];

        // Update sentiment for this specific game
        if (game.not_updated.includes('sentiment')) {
            updates.push(
                this.http.post(`http://localhost:8000/api/admin/sentiment/update/${game.id}`, {})
            );
        }

        // Generate tags for this specific game
        if (game.not_updated.includes('tags')) {
            updates.push(
                this.http.post(`http://localhost:8000/api/admin/review-tags/generate/${game.id}`, {})
            );
        }

        // Update Thai reviews for this specific game
        if (game.not_updated.includes('reviews')) {
            updates.push(
                this.http.post(`http://localhost:8000/api/admin/reviews/update/${game.id}`, {})
            );
        }

        if (updates.length === 0) {
            this.isAnyProcessing = false;
            return;
        }

        // Use forkJoin to run all updates in parallel
        import('rxjs').then(({ forkJoin }) => {
            forkJoin(updates).subscribe({
                next: () => {
                    this.isAnyProcessing = false;

                    this.messageService.add({
                        severity: 'success',
                        summary: 'อัปเดตเสร็จสิ้น',
                        detail: `อัปเดตข้อมูลสำหรับ ${game.title} เรียบร้อยแล้ว`,
                        life: 3000
                    });

                    // Reload the incomplete games list
                    this.loadDailyUpdateStatus();
                },
                error: (error) => {
                    this.isAnyProcessing = false;

                    this.messageService.add({
                        severity: 'error',
                        summary: 'เกิดข้อผิดพลาด',
                        detail: 'ไม่สามารถอัปเดตข้อมูลได้',
                        life: 5000
                    });
                }
            });
        });
    }

    fixAllIncompleteGames() {
        if (this.checkIfProcessing()) return;

        if (this.incompleteGames.length === 0) {
            this.messageService.add({
                severity: 'info',
                summary: 'ไม่มีเกมที่ต้องแก้ไข',
                detail: 'ทุกเกมมีข้อมูลครบถ้วนแล้ว',
                life: 3000
            });
            return;
        }

        this.isAnyProcessing = true;
        this.isFixingAll = true;

        this.messageService.add({
            severity: 'info',
            summary: 'เริ่มแก้ไขข้อมูลทั้งหมด',
            detail: `กำลังอัปเดตข้อมูลสำหรับ ${this.incompleteGames.length} เกม...`,
            life: 3000
        });

        // Use forkJoin to run all updates in parallel
        import('rxjs').then(({ forkJoin }) => {
            forkJoin([
                this.gameService.triggerSentimentUpdate(),
                this.gameService.triggerReviewTagsUpdate(),
                this.gameService.triggerReviewUpdate()
            ]).subscribe({
                next: (results) => {
                    this.isFixingAll = false;
                    this.isAnyProcessing = false;

                    // Reload incomplete games to see updated status
                    this.loadDailyUpdateStatus();

                    this.messageService.add({
                        severity: 'success',
                        summary: 'เริ่มการอัปเดตแล้ว',
                        detail: 'ระบบกำลังอัปเดตข้อมูลในเบื้องหลัง กรุณารอสักครู่...',
                        life: 5000
                    });
                },
                error: (error) => {
                    this.isFixingAll = false;
                    this.isAnyProcessing = false;

                    this.messageService.add({
                        severity: 'error',
                        summary: 'เกิดข้อผิดพลาด',
                        detail: 'ไม่สามารถอัปเดตข้อมูลได้ทั้งหมด',
                        life: 5000
                    });
                }
            });
        });
    }

    showAllIncomplete() {
        this.showAllIncompleteDialog = true;
    }

    checkUntaggedGames() {
        this.showUntaggedDialog = true;
        this.isCheckingUntagged = true;
        this.untaggedGames = [];

        this.gameService.getUntaggedGames().subscribe({
            next: (result: any) => {
                this.isCheckingUntagged = false;
                if (result.success) {
                    this.untaggedGames = result.games;

                    // if (this.untaggedGames.length === 0) {
                    //     this.messageService.add({
                    //         severity: 'success',
                    //         summary: 'Great!',
                    //         detail: 'ทุกเกมมีแท็กครบแล้ว !'
                    //     });
                    // }
                }
            },
            error: (err: any) => {
                this.isCheckingUntagged = false;
                this.messageService.add({
                    severity: 'error',
                    summary: 'Error',
                    detail: 'Failed to check untagged games'
                });
            }
        });
    }

    generateSingleTag(gameId: number) {
        // Check if any tag generation is already in progress
        const isAnyGenerating = Object.values(this.isGeneratingSingleTag).some(value => value === true);

        if (isAnyGenerating) {
            this.messageService.add({
                severity: 'warn',
                summary: 'กรุณารอสักครู่',
                detail: 'กำลังสร้างแท็กเกมอื่นอยู่ กรุณารอให้เสร็จก่อน',
                life: 3000
            });
            return;
        }

        this.isGeneratingSingleTag[gameId] = true;

        // Show progress toast (same as main generateTagsForGame)
        this.messageService.add({
            severity: 'info',
            summary: 'กำลังสร้างแท็ก',
            detail: 'กำลังวิเคราะห์รีวิวและสร้างแท็ก...',
            life: 3000
        });

        this.gameService.generateTagsForGame(gameId).subscribe({
            next: (result: any) => {
                this.isGeneratingSingleTag[gameId] = false;

                if (result.status === 'success') {
                    // Check if we actually got tags
                    const posCount = result.positive_tags?.length || 0;
                    const negCount = result.negative_tags?.length || 0;

                    if (posCount === 0 && negCount === 0) {
                        // Case: No reviews or analysis returned nothing
                        this.messageService.add({
                            severity: 'warn',
                            summary: 'ไม่พบรีวิว',
                            detail: 'เกมนี้ไม่มีรีวิวให้วิเคราะห์ หรือรีวิวไม่เพียงพอ'
                        });
                    } else {
                        // Case: Success with tags -> Show Result Dialog (same format as main flow)
                        const data = result.data || {};

                        // Get game name from result or find in untagged list
                        let gameName = data.game_name || result.game_name;
                        if (!gameName) {
                            const game = this.untaggedGames.find(g => g.id === gameId);
                            gameName = game?.title || `Game ${gameId}`;
                        }

                        this.showResultDialog('สร้างแท็กสำเร็จ', {
                            'เกม': gameName,
                            'แท็กแง่บวก': posCount,
                            'แท็กแง่ลบ': negCount,
                            'รีวิวที่วิเคราะห์': data.total_reviews_analyzed || 0
                        });

                        // Remove from list
                        this.untaggedGames = this.untaggedGames.filter(g => g.id !== gameId);
                    }
                } else if (result.status === 'warning') {
                    // Case: Explicit Warning from Backend
                    this.messageService.add({
                        severity: 'warn',
                        summary: 'ไม่พบรีวิว',
                        detail: 'เกมนี้ไม่มีรีวิวให้วิเคราะห์ หรือรีวิวไม่เพียงพอ'
                    });

                } else {
                    // Case: Error or Unhandled Warning
                    const msg = result.message || result.error || 'Failed to generate tags';

                    // Robust check: If backend didn't set status='warning' but message says "No English reviews"
                    if (msg && msg.includes('No English reviews')) {
                        this.messageService.add({
                            severity: 'warn',
                            summary: 'ไม่พบรีวิว',
                            detail: 'เกมนี้ไม่มีรีวิวให้วิเคราะห์ หรือรีวิวไม่เพียงพอ'
                        });
                    } else {
                        // Real Error
                        this.messageService.add({
                            severity: 'error',
                            summary: 'Error',
                            detail: msg
                        });
                    }
                }
            },
            error: (err: any) => {
                this.isGeneratingSingleTag[gameId] = false;
                this.messageService.add({
                    severity: 'error',
                    summary: 'Error',
                    detail: `Failed to generate tags for game ID ${gameId}`
                });
            }
        });
    }

    deleteGame() {
        if (this.checkIfProcessing()) return;

        if (!this.selectedGameId) {
            this.messageService.add({
                severity: 'warn',
                summary: 'กรุณาเลือกเกม',
                detail: 'กรุณาเลือกเกมที่ต้องการลบ',
                life: 3000
            });
            return;
        }

        this.showDeleteGameDialog = true;
    }

    confirmDeleteGame() {
        if (!this.selectedGameId) return;

        this.isDeletingGame = true;
        this.showDeleteGameDialog = false;

        this.gameService.deleteGame(this.selectedGameId).subscribe({
            next: (result: any) => {
                this.isDeletingGame = false;
                this.selectedGameId = null;
                this.loadGames(); // Refresh game list

                const deleted = result.deleted || {};
                this.showResultDialog('ลบเกมสำเร็จ', {
                    'เกม': deleted.game || 'ไม่ทราบชื่อ',
                    'ความคิดเห็น': deleted.comments || 0,
                    'รายการโปรด': deleted.favorites || 0,
                    'รีวิว': deleted.reviews || 0
                });
            },
            error: (err) => {
                this.isDeletingGame = false;
                this.messageService.add({
                    severity: 'error',
                    summary: 'ลบเกมล้มเหลว',
                    detail: err.error?.detail || 'เกิดข้อผิดพลาดในการลบเกม',
                    life: 5000
                });
            }
        });
    }

    cancelDeleteGame() {
        this.showDeleteGameDialog = false;
    }

    getTagStatusLabel(status: string | null | undefined): string {
        switch (status) {
            case 'success': return 'อัปเดตแล้ว';
            case 'insufficient': return 'รีวิวน้อยเกินไป (<5)';
            case 'insufficient_english': return 'รีวิว Eng น้อยเกินไป';
            case 'no_reviews': return 'ไม่มีรีวิว (0)';
            case 'no_english_reviews': return 'ไม่มีรีวิวภาษาอังกฤษ';
            case 'error': return 'Error';
            default: return 'Tags ยังไม่อัปเดต';
        }
    }

    getTagStatusClass(status: string | null | undefined): string {
        switch (status) {
            case 'success': return 'bg-green-100 text-green-700';
            case 'insufficient': return 'bg-yellow-100 text-yellow-700';
            case 'insufficient_english': return 'bg-orange-100 text-orange-700';
            case 'no_reviews': return 'bg-yellow-100 text-yellow-700';
            case 'no_english_reviews': return 'bg-orange-100 text-orange-700';
            case 'error': return 'bg-red-100 text-red-700';
            default: return 'bg-orange-100 text-orange-700';
        }
    }

    getTagStatusIcon(status: string | null | undefined): string {
        switch (status) {
            case 'success': return 'pi pi-check';
            case 'insufficient': return 'pi pi-exclamation-triangle';
            case 'insufficient_english': return 'pi pi-globe';
            case 'no_reviews': return 'pi pi-info-circle';
            case 'no_english_reviews': return 'pi pi-globe';
            case 'error': return 'pi pi-times';
            default: return 'pi pi-clock';
        }
    }
}

