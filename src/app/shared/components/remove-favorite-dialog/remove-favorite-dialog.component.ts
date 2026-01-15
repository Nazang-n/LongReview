import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DialogModule } from 'primeng/dialog';

@Component({
    selector: 'app-remove-favorite-dialog',
    standalone: true,
    imports: [CommonModule, DialogModule],
    template: `
    <p-dialog [(visible)]="visible" [modal]="true" [style]="{width: '500px'}" [draggable]="false"
        [resizable]="false" [closable]="false" (onHide)="onDialogHide()">
      <ng-template pTemplate="header">
        <div class="flex items-center gap-3">
          <i class="pi pi-heart-fill text-red-600 text-2xl"></i>
          <span class="font-bold text-xl">ลบออกจากรายการโปรด</span>
        </div>
      </ng-template>
      <div class="py-4">
        <p class="text-gray-700 text-lg">
          คุณต้องการลบ <strong class="text-purple-600">{{ gameTitle }}</strong> ออกจากรายการโปรดหรือไม่?
        </p>
      </div>
      <ng-template pTemplate="footer">
        <button (click)="onCancel()"
          class="px-4 py-2 bg-gray-300 hover:bg-gray-400 text-gray-800 rounded-lg transition-colors font-medium">
          ยกเลิก
        </button>
        <button (click)="onConfirm()"
          class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors font-medium">
          <i class="pi pi-heart-fill mr-2"></i>
          ลบออกจากรายการโปรด
        </button>
      </ng-template>
    </p-dialog>
  `
})
export class RemoveFavoriteDialogComponent {
    @Input() visible: boolean = false;
    @Input() gameTitle: string = '';

    @Output() visibleChange = new EventEmitter<boolean>();
    @Output() confirm = new EventEmitter<void>();
    @Output() cancel = new EventEmitter<void>();

    onDialogHide() {
        this.visible = false;
        this.visibleChange.emit(false);
    }

    onConfirm() {
        this.confirm.emit();
    }

    onCancel() {
        this.cancel.emit();
    }
}
