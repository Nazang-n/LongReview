import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HeaderComponent } from '../shared/header.component';
import { FooterComponent } from '../shared/footer.component';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { MessageModule } from 'primeng/message';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { NewsService } from '../services/news.service';

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
export class AdminComponent {
    isLoading = false;
    syncResult: any = null;
    error: string | null = null;

    constructor(private newsService: NewsService) { }

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
}
