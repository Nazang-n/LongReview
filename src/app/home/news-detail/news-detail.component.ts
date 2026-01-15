import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { HeaderComponent } from '../../shared/header.component';
import { FooterComponent } from '../../shared/footer.component';
import { NewsService, NewsItem } from '../../services/news.service';
import { DialogModule } from 'primeng/dialog';

@Component({
    selector: 'app-news-detail',
    standalone: true,
    imports: [CommonModule, RouterModule, HeaderComponent, FooterComponent, DialogModule],
    templateUrl: './news-detail.component.html',
    styleUrls: ['./news-detail.component.css']
})
export class NewsDetailComponent implements OnInit {
    newsId: string = '';
    newsItem: NewsItem | null = null;
    relatedNews: NewsItem[] = [];
    isLoading: boolean = true;
    error: string | null = null;
    showCopySuccessDialog: boolean = false;

    constructor(
        private route: ActivatedRoute,
        private router: Router,
        private newsService: NewsService
    ) { }

    ngOnInit() {
        this.route.params.subscribe(params => {
            this.newsId = params['id'];
            this.loadNewsDetail();
        });
    }

    loadNewsDetail() {
        this.isLoading = true;
        this.error = null;

        // Fetch all news and find the one with matching ID
        this.newsService.getNews().subscribe({
            next: (response) => {
                this.newsItem = response.news.find(news => news.id === this.newsId) || null;

                if (!this.newsItem) {
                    this.error = 'ไม่พบข่าวที่คุณต้องการ';
                } else {
                    // Load random news (exclude current news)
                    const otherNews = response.news.filter(news => news.id !== this.newsId);

                    // Shuffle array using Fisher-Yates algorithm
                    for (let i = otherNews.length - 1; i > 0; i--) {
                        const j = Math.floor(Math.random() * (i + 1));
                        [otherNews[i], otherNews[j]] = [otherNews[j], otherNews[i]];
                    }

                    // Take first 3 random items
                    this.relatedNews = otherNews.slice(0, 3);
                }

                this.isLoading = false;
            },
            error: (err) => {
                this.error = err.message || 'ไม่สามารถโหลดข่าวได้';
                this.isLoading = false;
            }
        });
    }

    goBack() {
        this.router.navigate(['/news']);
    }

    openOriginalArticle() {
        if (this.newsItem?.link) {
            window.open(this.newsItem.link, '_blank');
        }
    }

    shareOnFacebook() {
        if (this.newsItem?.link) {
            const url = encodeURIComponent(this.newsItem.link);
            window.open(`https://www.facebook.com/sharer/sharer.php?u=${url}`, '_blank');
        }
    }

    shareOnTwitter() {
        if (this.newsItem?.link && this.newsItem?.title) {
            const url = encodeURIComponent(this.newsItem.link);
            const text = encodeURIComponent(this.newsItem.title);
            window.open(`https://twitter.com/intent/tweet?url=${url}&text=${text}`, '_blank');
        }
    }

    copyLink() {
        if (this.newsItem?.link) {
            navigator.clipboard.writeText(this.newsItem.link).then(() => {
                this.showCopySuccessDialog = true;
            });
        }
    }
}
