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
        DialogModule
    ],
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

    constructor(
        private newsService: NewsService,
        private gameService: GameService,
        private commentService: CommentService,
        private authService: AuthService
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

        this.gameService.triggerReviewUpdate().subscribe({
            next: (result) => {
                this.reviewUpdateResult = result;
                this.isUpdatingReviews = false;
            },
            error: (err) => {
                this.reviewUpdateError = err.message || 'Failed to trigger review update';
                this.isUpdatingReviews = false;
            }
        });
    }

    triggerSentimentUpdate() {
        this.isUpdatingSentiment = true;
        this.sentimentUpdateResult = null;
        this.sentimentUpdateError = null;

        this.gameService.triggerSentimentUpdate().subscribe({
            next: (result: any) => {
                this.sentimentUpdateResult = result;
                this.isUpdatingSentiment = false;
            },
            error: (err: any) => {
                this.sentimentUpdateError = err.message || 'Failed to trigger sentiment update';
                this.isUpdatingSentiment = false;
            }
        });
    }

    triggerReviewTagsUpdate() {
        this.isUpdatingReviewTags = true;
        this.reviewTagsUpdateResult = null;
        this.reviewTagsUpdateError = null;

        this.gameService.triggerReviewTagsUpdate().subscribe({
            next: (result: any) => {
                this.reviewTagsUpdateResult = result;
                this.isUpdatingReviewTags = false;
            },
            error: (err: any) => {
                this.reviewTagsUpdateError = err.message || 'Failed to trigger review tags update';
                this.isUpdatingReviewTags = false;
            }
        });
    }
}
