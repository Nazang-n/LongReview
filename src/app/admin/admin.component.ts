import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HeaderComponent } from '../shared/header.component';
import { FooterComponent } from '../shared/footer.component';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { MessageModule } from 'primeng/message';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { NewsService } from '../services/news.service';
import { CommentService, CommentReport } from '../services/comment.service';
import { AuthService } from '../services/auth.service';

@Component({
    selector: 'app-admin',
    standalone: true,
    imports: [
        CommonModule,
        HeaderComponent,
        FooterComponent,
        ButtonModule,
        CardModule,
        MessageModule,
        ProgressSpinnerModule
    ],
    templateUrl: './admin.component.html',
    styleUrls: ['./admin.component.css']
})
export class AdminComponent implements OnInit {
    isLoading = false;
    syncResult: any = null;
    error: string | null = null;

    // Comment reports
    reportedComments: CommentReport[] = [];
    isLoadingReports = false;
    reportsError: string | null = null;

    constructor(
        private newsService: NewsService,
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
        const user = this.authService.getCurrentUserValue();
        if (!user) return;

        if (confirm('คุณต้องการยกเลิกรายงานนี้หรือไม่?')) {
            this.commentService.dismissReport(reportId, user.id).subscribe({
                next: () => {
                    this.loadReportedComments();
                },
                error: (err) => {
                    console.error('Error dismissing report:', err);
                    alert('เกิดข้อผิดพลาดในการยกเลิกรายงาน');
                }
            });
        }
    }

    deleteReportedComment(commentId: number) {
        const user = this.authService.getCurrentUserValue();
        if (!user) return;

        if (confirm('คุณต้องการลบความคิดเห็นนี้หรือไม่? การลบจะลบรายงานทั้งหมดที่เกี่ยวข้องด้วย')) {
            this.commentService.deleteComment(commentId, user.id).subscribe({
                next: () => {
                    this.loadReportedComments();
                },
                error: (err) => {
                    console.error('Error deleting comment:', err);
                    alert('เกิดข้อผิดพลาดในการลบความคิดเห็น');
                }
            });
        }
    }
}
