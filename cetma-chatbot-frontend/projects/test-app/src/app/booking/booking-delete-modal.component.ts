import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { Booking, BookingService } from '../services/booking.service';

@Component({
  selector: 'app-booking-delete-modal',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="modal-overlay" *ngIf="isVisible" (click)="onCancel()">
      <div class="modal-container" (click)="$event.stopPropagation()">
        <div class="modal-header">
          <div class="warning-icon">⚠️</div>
          <h2>Conferma Eliminazione</h2>
        </div>

        <div class="modal-content" *ngIf="booking">
          <p class="warning-text">
            Sei sicuro di voler eliminare definitivamente questa prenotazione?
          </p>

          <div class="booking-summary">
            <div class="summary-item">
              <span class="label">Visitatore:</span>
              <span class="value">{{ booking.visitor_name }}</span>
            </div>
            <div class="summary-item">
              <span class="label">Area:</span>
              <span class="value">{{ booking.booking_area }}</span>
            </div>
            <div class="summary-item">
              <span class="label">Data e Orario:</span>
              <span class="value">{{ formatDate(booking.booking_date) }} alle {{ booking.booking_time }}</span>
            </div>
            <div class="summary-item">
              <span class="label">Status:</span>
              <span class="value status" [class]="getStatusClass(booking.status)">
                {{ getStatusLabel(booking.status) }}
              </span>
            </div>
          </div>

          <div class="danger-notice">
            <strong>⚠️ Attenzione:</strong> Questa azione non può essere annullata. 
            La prenotazione verrà eliminata definitivamente dal database.
          </div>
        </div>

        <div class="modal-actions">
          <button 
            type="button" 
            class="btn-cancel" 
            (click)="onCancel()"
            [disabled]="isDeleting"
          >
            Annulla
          </button>
          <button 
            type="button" 
            class="btn-delete" 
            (click)="onConfirmDelete()"
            [disabled]="isDeleting"
          >
            <span *ngIf="isDeleting" class="spinner"></span>
            {{ isDeleting ? 'Eliminando...' : 'Elimina Definitivamente' }}
          </button>
        </div>

        <div class="error-message" *ngIf="errorMessage">
          {{ errorMessage }}
        </div>
      </div>
    </div>
  `,
  styles: [`
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600&display=swap');

    .modal-overlay {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
      padding: 1rem;
    }

    .modal-container {
      background: white;
      border-radius: 12px;
      width: 100%;
      max-width: 500px;
      box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
      font-family: 'Montserrat', sans-serif;
    }

    .modal-header {
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 1.5rem;
      border-bottom: 1px solid #e5e7eb;
      background: #fef2f2;
      border-radius: 12px 12px 0 0;

      .warning-icon {
        font-size: 2rem;
        color: #dc2626;
      }

      h2 {
        color: #dc2626;
        font-weight: 600;
        margin: 0;
        font-size: 1.5rem;
      }
    }

    .modal-content {
      padding: 1.5rem;

      .warning-text {
        font-size: 1.1rem;
        color: #374151;
        margin-bottom: 1.5rem;
        font-weight: 500;
        text-align: center;
      }

      .booking-summary {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1.5rem;
        border: 1px solid #e5e7eb;

        .summary-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.5rem 0;
          border-bottom: 1px solid #e5e7eb;

          &:last-child {
            border-bottom: none;
          }

          .label {
            font-weight: 500;
            color: #666;
            font-size: 0.9rem;
          }

          .value {
            font-weight: 600;
            color: #374151;
            text-align: right;
            flex: 1;
            margin-left: 1rem;

            &.status {
              padding: 0.25rem 0.5rem;
              border-radius: 12px;
              font-size: 0.8rem;
              text-transform: uppercase;
              letter-spacing: 0.5px;

              &.status-pending {
                background: #fef3c7;
                color: #d97706;
              }

              &.status-confirmed {
                background: #d1fae5;
                color: #059669;
              }

              &.status-cancelled {
                background: #fee2e2;
                color: #dc2626;
              }
            }
          }
        }
      }

      .danger-notice {
        background: #fef2f2;
        border: 1px solid #fecaca;
        border-radius: 8px;
        padding: 1rem;
        color: #dc2626;
        font-size: 0.9rem;
        line-height: 1.5;

        strong {
          font-weight: 600;
        }
      }
    }

    .modal-actions {
      display: flex;
      gap: 1rem;
      justify-content: flex-end;
      padding: 1.5rem;
      border-top: 1px solid #e5e7eb;
      background: #f8f9fa;
      border-radius: 0 0 12px 12px;
    }

    .btn-cancel, .btn-delete {
      padding: 0.75rem 1.5rem;
      border: none;
      border-radius: 8px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-family: inherit;

      &:disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }
    }

    .btn-cancel {
      background: white;
      color: #374151;
      border: 1px solid #e5e7eb;

      &:hover:not(:disabled) {
        background: #f9fafb;
        border-color: #d1d5db;
      }
    }

    .btn-delete {
      background: #dc2626;
      color: white;

      &:hover:not(:disabled) {
        background: #b91c1c;
      }
    }

    .spinner {
      width: 16px;
      height: 16px;
      border: 2px solid rgba(255, 255, 255, 0.3);
      border-top: 2px solid white;
      border-radius: 50%;
      animation: spin 1s linear infinite;
    }

    .error-message {
      color: #dc2626;
      font-size: 0.9rem;
      margin: 0 1.5rem 1rem;
      padding: 0.75rem;
      background: #fef2f2;
      border-radius: 6px;
      font-weight: 500;
      text-align: center;
    }

    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  `]
})
export class BookingDeleteModalComponent {
  @Input() isVisible = false;
  @Input() booking: Booking | null = null;
  @Output() bookingDeleted = new EventEmitter<number>();
  @Output() cancelled = new EventEmitter<void>();

  isDeleting = false;
  errorMessage = '';

  constructor(private bookingService: BookingService) {}

  onConfirmDelete() {
    if (this.booking) {
      this.isDeleting = true;
      this.errorMessage = '';

      this.bookingService.deleteBooking(this.booking.id).subscribe({
        next: (response) => {
          if (response.success) {
            this.bookingDeleted.emit(this.booking!.id);
            this.onCancel();
          } else {
            this.errorMessage = response.message || 'Errore durante l\'eliminazione';
          }
          this.isDeleting = false;
        },
        error: (error) => {
          console.error('Errore delete:', error);
          this.errorMessage = 'Errore durante l\'eliminazione della prenotazione';
          this.isDeleting = false;
        }
      });
    }
  }

  onCancel() {
    this.errorMessage = '';
    this.isDeleting = false;
    this.cancelled.emit();
  }

  formatDate(dateString: string): string {
    let date: Date;

    // Controlla se il formato è dd/mm/yyyy
    if (/^\d{2}\/\d{2}\/\d{4}$/.test(dateString)) {
      const [day, month, year] = dateString.split('/');
      date = new Date(Number(year), Number(month) - 1, Number(day));
    } else {
      date = new Date(dateString);
    }

    if (isNaN(date.getTime())) {
      return dateString; // Ritorna la stringa originale se non riesce a parsare
    }

    return date.toLocaleDateString('it-IT', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }

  getStatusClass(status: string): string {
    switch (status) {
      case 'confirmed': return 'status-confirmed';
      case 'cancelled': return 'status-cancelled';
      default: return 'status-pending';
    }
  }

  getStatusLabel(status: string): string {
    switch (status) {
      case 'confirmed': return 'Confermata';
      case 'cancelled': return 'Annullata';
      default: return 'In Attesa';
    }
  }
}