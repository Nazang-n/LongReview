import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { HeaderComponent } from '../../shared/header.component';
import { FooterComponent } from '../../shared/footer.component';

@Component({
    selector: 'app-game-detail',
    standalone: true,
    imports: [CommonModule, HeaderComponent, FooterComponent],
    templateUrl: './game-detail.component.html',
    styleUrls: ['./game-detail.component.css']
})
export class GameDetailComponent implements OnInit {
    gameId: string | null = '';

    constructor(private route: ActivatedRoute) { }

    ngOnInit() {
        // รับค่า ID จาก URL มาแสดง
        this.gameId = this.route.snapshot.paramMap.get('id');
    }
}
