import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { HeaderComponent } from '../../shared/header.component';
import { FooterComponent } from '../../shared/footer.component';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { TagModule } from 'primeng/tag';
import { DividerModule } from 'primeng/divider';
import { NewsService, NewsItem } from '../../services/news.service';

@Component({
    selector: 'app-news',
    standalone: true,
    imports: [CommonModule, RouterModule, FooterComponent, ButtonModule, CardModule, TagModule, DividerModule],
    templateUrl: './news.component.html',
    styleUrls: ['./news.component.css']
})
export class NewsComponent implements OnInit {
    featuredNews: NewsItem | null = null;
    sideNews: NewsItem[] = [];
    latestNews: NewsItem[] = [];

    isLoading: boolean = true;
    isLoadingMore: boolean = false;
    error: string | null = null;
    nextPage: string | null = null;

    constructor(private newsService: NewsService) { }

    ngOnInit() {
        this.loadNews();
    }

    loadNews() {
        this.isLoading = true;
        this.error = null;

        this.newsService.getNews().subscribe({
            next: (response) => {
                if (response.news.length > 0) {
                    // First news as featured
                    this.featuredNews = response.news[0];

                    // Next 2 as side news
                    this.sideNews = response.news.slice(1, 3);

                    // Rest as latest news
                    this.latestNews = response.news.slice(3);

                    // Store nextPage token for pagination
                    this.nextPage = response.nextPage || null;
                }
                this.isLoading = false;
            },
            error: (err) => {
                this.error = err.message || 'ไม่สามารถโหลดข่าวได้ กรุณาลองใหม่อีกครั้ง';
                this.isLoading = false;
                console.error('Error loading news:', err);
            }
        });
    }

    loadMore() {
        if (!this.nextPage || this.isLoadingMore) {
            return;
        }

        this.isLoadingMore = true;
        this.error = null;

        // Calculate skip based on current news count
        const currentCount = this.latestNews.length + this.sideNews.length + 1; // +1 for featured

        this.newsService.getNews(null, currentCount).subscribe({
            next: (response) => {
                // Append new news to latest news
                this.latestNews = [...this.latestNews, ...response.news];

                // Update nextPage based on hasMore
                this.nextPage = response.hasMore ? 'more' : null;

                this.isLoadingMore = false;
            },
            error: (err) => {
                this.error = err.message || 'ไม่สามารถโหลดข่าวเพิ่มเติมได้';
                this.isLoadingMore = false;
                console.error('Error loading more news:', err);
            }
        });
    }

    retry() {
        this.loadNews();
    }
}
