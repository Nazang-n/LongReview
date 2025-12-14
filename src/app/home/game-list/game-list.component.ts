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
    selector: 'app-game-list',
    standalone: true,
    imports: [CommonModule, RouterModule, HeaderComponent, FooterComponent],
    templateUrl: './game-list.component.html',
    styleUrls: ['./game-list.component.css']
})
export class GameListComponent {
    isFilterOpen = true;

    games: Game[] = [
        {
            id: 1,
            title: 'Apex Legends',
            description: 'เกมที่ผสมผสาน Battle Royale ที่มีตัวละครที่แตกต่างกันความสามารถของแต่ละตัวละครที่',
            releaseDate: '4 ตุลาคม 2562',
            genres: ['Battle Royale', 'FPS'],
            reviewTags: ['ยิงปืน', 'เกมไว'],
            image: 'https://cdn.cloudflare.steamstatic.com/steam/apps/1172470/header.jpg',
            reviewType: 'positive',
            isNew: false
        },
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
            id: 4,
            title: 'Forza Horizon 5',
            description: 'เกมแข่งรถโอเพ่นเวิลด์ในประเทศเม็กซิโกที่มีภูมิทัศน์ที่สวยงาม',
            releaseDate: '9 พฤศจิกายน 2564',
            genres: ['แข่งรถ', 'โอเพ่นเวิลด์'],
            reviewTags: ['สนุก', 'ผ่อนคลาย'],
            image: 'https://cdn.akamai.steamstatic.com/steam/apps/1551360/header.jpg',
            reviewType: 'mixed',
            isNew: false
        },
        {
            id: 5,
            title: 'FIFA 24',
            description: 'เกมฟุตบอลจากอีเอสปอร์ตที่มีทีม Ultimate Team',
            releaseDate: '29 กันยายน 2566',
            genres: ['กีฬา', 'ฟุตบอล'],
            reviewTags: ['ซ้ำซาก', 'Pay to Win'],
            image: 'https://cdn.cloudflare.steamstatic.com/steam/apps/2195250/header.jpg',
            reviewType: 'mixed',
            isNew: true
        },
        {
            id: 6,
            title: 'Cyberpunk 2077',
            description: 'เกม RPG โอเพ่นเวิลด์ในโลคาอนาคต Night City จาก CD Projekt Red',
            releaseDate: '10 ธันวาคม 2563',
            genres: ['RPG', 'โอเพ่นเวิลด์'],
            reviewTags: ['บั๊กเยอะ', 'เนื้อเรื่องดี'],
            image: 'https://image.api.playstation.com/vulcan/ap/rnd/202111/3013/cKZ4tKNFj9C00giTzYtH8PF1.png',
            reviewType: 'mixed',
            isNew: false
        },
        {
            id: 7,
            title: 'Halo Infinite',
            description: 'เกม FPS จากซีรีส์ Halo ที่กลับมาพร้อมโหมด Multiplayer ฟรี',
            releaseDate: '8 ธันวาคม 2564',
            genres: ['FPS', 'Multiplayer'],
            reviewTags: ['ยิงปืน', 'ฟรี'],
            image: 'https://cdn.cloudflare.steamstatic.com/steam/apps/1240440/header.jpg',
            reviewType: 'positive',
            isNew: false
        },
        {
            id: 8,
            title: 'Starfield',
            description: 'เกม RPG อวกาศจาก Bethesda ที่ให้คุณสำรวจกาแล็กซี',
            releaseDate: '6 กันยายน 2566',
            genres: ['RPG', 'อวกาศ'],
            reviewTags: ['น่าเบื่อ', 'ช้า'],
            image: 'https://cdn.akamai.steamstatic.com/steam/apps/1716740/header.jpg',
            reviewType: 'negative',
            isNew: true
        },
        {
            id: 9,
            title: 'The Last of Us Part II',
            description: 'เกม Action-Adventure ที่เล่าเรื่องราวของ Ellie ในโลกหลังวันสิ้นโลก',
            releaseDate: '19 มิถุนายน 2563',
            genres: ['Action', 'ผจญภัย'],
            reviewTags: ['เนื้อเรื่องดี', 'อารมณ์หนัก'],
            image: 'https://image.api.playstation.com/vulcan/img/rnd/202010/2618/Y02ljdBodKFBiziorYgqftLE.png',
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
            id: 13,
            title: 'Hogwarts Legacy',
            description: 'เกม RPG โลก Harry Potter ที่ให้คุณเป็นนักเรียนฮอกวอตส์',
            releaseDate: '10 กุมภาพันธ์ 2566',
            genres: ['RPG', 'โอเพ่นเวิลด์'],
            reviewTags: ['สำรวจได้เยอะ', 'มีเสน่ห์'],
            image: 'https://cdn.cloudflare.steamstatic.com/steam/apps/990080/header.jpg',
            reviewType: 'mixed',
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
        }
    ];

    toggleFilter() {
        this.isFilterOpen = !this.isFilterOpen;
    }
}
