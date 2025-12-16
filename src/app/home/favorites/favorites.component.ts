import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { HeaderComponent } from '../../shared/header.component';
import { FooterComponent } from '../../shared/footer.component';

interface Game {
    id: number;
    title: string;
    description: string;
    releaseDate: string;
    genres: string[];
    reviewTags: string[];
    image: string;
    reviewType: 'positive' | 'negative' | 'mixed';
    isNew?: boolean;
}

@Component({
    selector: 'app-favorites',
    standalone: true,
    imports: [CommonModule, RouterModule, HeaderComponent, FooterComponent],
    templateUrl: './favorites.component.html',
    styleUrls: ['./favorites.component.css']
})
export class FavoritesComponent {
    favoriteGames: Game[] = [
        {
            id: 2,
            title: 'Elden Ring',
            description: 'เกม Action RPG โอเพ่นเวิลด์จากทีมสร้าง Dark Souls ร่วมกับ George R.R. Martin',
            releaseDate: '25 กุมภาพันธ์ 2565',
            genres: ['Action RPG', 'โอเพ่นเวิลด์'],
            reviewTags: ['ยาก', 'ท้าทาย'],
            image: 'https://image.api.playstation.com/vulcan/ap/rnd/202110/2000/aGhopp3MHppi7kooGE2Dtt8C.png',
            reviewType: 'positive',
            isNew: false
        },
        {
            id: 3,
            title: 'God of War Ragnarök',
            description: 'ภาคต่อของ God of War 2018 ที่ชวนให้ไปสำรวจนอร์ดิก',
            releaseDate: '9 พฤศจิกายน 2565',
            genres: ['Action', 'ผจญภัย'],
            reviewTags: ['เนื้อเรื่องดี', 'กราฟิกสวย'],
            image: 'https://image.api.playstation.com/vulcan/ap/rnd/202207/1210/4xJ8XB3bi888QTLZYdl7Oi0s.png',
            reviewType: 'positive',
            isNew: false
        },
        {
            id: 11,
            title: 'Baldur\'s Gate 3',
            description: 'เกม RPG แนว D&D ที่ให้เสรีภาพในการเล่นสูงมาก',
            releaseDate: '3 สิงหาคม 2566',
            genres: ['RPG', 'กลยุทธ์'],
            reviewTags: ['เนื้อหาเยอะ', 'เล่นซ้ำได้'],
            image: 'https://cdn.cloudflare.steamstatic.com/steam/apps/1086940/header.jpg',
            reviewType: 'positive',
            isNew: true
        },
        {
            id: 12,
            title: 'Resident Evil 4 Remake',
            description: 'รีเมคของเกมสยองขวัญคลาสสิกที่ได้รับการปรับปรุงใหม่',
            releaseDate: '24 มีนาคม 2566',
            genres: ['สยองขวัญ', 'Action'],
            reviewTags: ['น่ากลัว', 'ตื่นเต้น'],
            image: 'https://cdn.cloudflare.steamstatic.com/steam/apps/2050650/header.jpg',
            reviewType: 'positive',
            isNew: false
        },
        {
            id: 14,
            title: 'Red Dead Redemption 2',
            description: 'เกมคาวบอยโอเพ่นเวิลด์ที่มีรายละเอียดสูงมาก',
            releaseDate: '26 ตุลาคม 2561',
            genres: ['Action', 'โอเพ่นเวิลด์'],
            reviewTags: ['เนื้อเรื่องดี', 'โลกกว้าง'],
            image: 'https://cdn.cloudflare.steamstatic.com/steam/apps/1174180/header.jpg',
            reviewType: 'positive',
            isNew: false
        },
        {
            id: 10,
            title: 'Spider-Man 2',
            description: 'ภาคต่อของ Spider-Man ที่ให้คุณเล่นได้ทั้ง Peter Parker และ Miles Morales',
            releaseDate: '20 ตุลาคม 2566',
            genres: ['Action', 'ผจญภัย'],
            reviewTags: ['สนุก', 'กราฟิกสวย'],
            image: 'https://image.api.playstation.com/vulcan/ap/rnd/202306/1219/1c7b75d8ed9271516546560d219ad0b22ee0a263b4537bd8.png',
            reviewType: 'positive',
            isNew: true
        }
    ];
}
