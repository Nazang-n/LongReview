import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
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
        ToastModule
    ],
    providers: [MessageService],
    templateUrl: './admin.component.html',
    styleUrls: ['./admin.component.css']
})
export class AdminComponent implements OnInit {
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
    pendingReportId: number | null = null;
    pendingCommentId: number | null = null;

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

    // Polling intervals
    private pollingIntervals: Map<string, any> = new Map();

    constructor(
        private newsService: NewsService,
        private gameService: GameService,
        private commentService: CommentService,
        private authService: AuthService,
        private messageService: MessageService
    ) { }

    ngOnInit() {
        this.loadReportedComments();
    }

    syncNews() {
        this.isLoading = true;
        this.syncResult = null;
        this.error = null;

        this.newsService.syncNews().subscribe({
            next: (result) => {
                this.syncResult = result;
                this.isLoading = false;
            },
            error: (err) => {
                this.error = err.message || 'Failed to sync news';
                this.isLoading = false;
            }
        });
    }

    translateGames() {
        this.isTranslating = true;
        this.translateResult = null;
        this.translateError = null;

        this.gameService.batchTranslateGames().subscribe({
            next: (result: any) => {
                this.translateResult = result;
                this.isTranslating = false;
                console.log('Translation result:', result);
            },
            error: (err: any) => {
                this.translateError = err.message || 'Failed to translate games';
                this.isTranslating = false;
                console.error('Translation error:', err);
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
        this.isUpdatingReviews = true;
        this.reviewUpdateResult = null;
        this.reviewUpdateError = null;

        this.messageService.add({
            severity: 'info',
            summary: 'Thai Review Update Started',
            detail: 'Fetching Thai reviews in background. You will be notified when complete.',
            life: 3000
        });

        this.gameService.triggerReviewUpdate().subscribe({
            next: (result) => {
                this.reviewUpdateResult = result;
                this.isUpdatingReviews = false;

                // Build detailed message from stats
                const stats = result.stats || {};
                const detailMessage = `✓ Games: ${stats.games_processed || 0} processed\n✓ Successful: ${stats.successful || 0}\n✗ Failed: ${stats.failed || 0}\n📝 New reviews: ${stats.total_new_reviews || 0}`;

                // Show success toast with statistics
                this.messageService.add({
                    severity: 'success',
                    summary: 'Thai Reviews Updated!',
                    detail: detailMessage,
                    life: 8000  // Longer duration for detailed info
                });
            },
            error: (err) => {
                this.reviewUpdateError = err.message || 'Failed to trigger review update';
                this.isUpdatingReviews = false;

                // Show error toast
                this.messageService.add({
                    severity: 'error',
                    summary: 'Update Failed',
                    detail: this.reviewUpdateError || undefined,
                    life: 5000
                });
            }
        });
    }

    triggerSentimentUpdate() {
        this.isUpdatingSentiment = true;
        this.sentimentUpdateResult = null;
        this.sentimentUpdateError = null;

        this.messageService.add({
            severity: 'info',
            summary: 'Sentiment Update Started',
            detail: 'Updating game sentiments in background. You will be notified when complete.',
            life: 3000
        });

        this.gameService.triggerSentimentUpdate().subscribe({
            next: (result: any) => {
                this.sentimentUpdateResult = result;
                this.isUpdatingSentiment = false;

                // Build detailed message from stats
                const stats = result.stats || {};
                const detailMessage = `✓ Games processed: ${stats.games_processed || 0}\n✓ Updated: ${stats.updated || 0}\n✗ Errors: ${stats.errors || 0}`;

                // Show success toast with statistics
                this.messageService.add({
                    severity: 'success',
                    summary: 'Sentiments Updated!',
                    detail: detailMessage,
                    life: 8000
                });
            },
            error: (err: any) => {
                this.sentimentUpdateError = err.message || 'Failed to trigger sentiment update';
                this.isUpdatingSentiment = false;

                // Show error toast
                this.messageService.add({
                    severity: 'error',
                    summary: 'Update Failed',
                    detail: this.sentimentUpdateError || undefined,
                    life: 5000
                });
            }
        });
    }

    triggerReviewTagsUpdate() {
        this.isUpdatingReviewTags = true;
        this.reviewTagsUpdateResult = null;
        this.reviewTagsUpdateError = null;

        this.messageService.add({
            severity: 'info',
            summary: 'Review Tags Update Started',
            detail: 'Generating review tags in background. You will be notified when complete.',
            life: 3000
        });

        this.gameService.triggerReviewTagsUpdate().subscribe({
            next: (result: any) => {
                this.reviewTagsUpdateResult = result;
                this.isUpdatingReviewTags = false;

                // Build detailed message from stats
                const stats = result.stats || {};
                const detailMessage = `✓ Games checked: ${stats.games_checked || 0}\n✓ Updated: ${stats.updated || 0}\n⊘ Skipped: ${stats.skipped || 0}\n✗ Errors: ${stats.errors || 0}`;

                // Show success toast with statistics
                this.messageService.add({
                    severity: 'success',
                    summary: 'Review Tags Updated!',
                    detail: detailMessage,
                    life: 8000
                });
            },
            error: (err: any) => {
                this.reviewTagsUpdateError = err.message || 'Failed to trigger review tags update';
                this.isUpdatingReviewTags = false;

                // Show error toast
                this.messageService.add({
                    severity: 'error',
                    summary: 'Update Failed',
                    detail: this.reviewTagsUpdateError || undefined,
                    life: 5000
                });
            }
        });
    }
}

