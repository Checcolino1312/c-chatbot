import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, OnInit, Output, OnChanges } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Booking, BookingService } from '../services/booking.service';

@Component({
  selector: 'app-booking-edit-modal',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="modal-overlay" *ngIf="isVisible" (click)="onCancel()">
      <div class="modal-container" (click)="$event.stopPropagation()">
        <div class="modal-header">
          <h2>✏️ Modifica Prenotazione</h2>
          <button class="close-btn" (click)="onCancel()" type="button">×</button>
        </div>

        <form [formGroup]="editForm" (ngSubmit)="onSubmit()" class="edit-form">
          <!-- Informazioni Visitatore -->
          <div class="form-section">
            <h3>👤 Informazioni Visitatore</h3>
            
            <div class="form-group">
              <label for="visitor_name">Nome Completo *</label>
              <input 
                type="text" 
                id="visitor_name"
                formControlName="visitor_name"
                [class.error]="isFieldInvalid('visitor_name')"
              >
              <div class="error-message" *ngIf="isFieldInvalid('visitor_name')">
                Nome è obbligatorio
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label for="visitor_email">Email *</label>
                <input 
                  type="email" 
                  id="visitor_email"
                  formControlName="visitor_email"
                  [class.error]="isFieldInvalid('visitor_email')"
                >
                <div class="error-message" *ngIf="isFieldInvalid('visitor_email')">
                  <span *ngIf="editForm.get('visitor_email')?.errors?.['required']">Email è obbligatoria</span>
                  <span *ngIf="editForm.get('visitor_email')?.errors?.['email']">Email non valida</span>
                </div>
              </div>

              <div class="form-group">
                <label for="visitor_phone">Telefono *</label>
                <input 
                  type="tel" 
                  id="visitor_phone"
                  formControlName="visitor_phone"
                  [class.error]="isFieldInvalid('visitor_phone')"
                >
                <div class="error-message" *ngIf="isFieldInvalid('visitor_phone')">
                  Telefono è obbligatorio
                </div>
              </div>
            </div>
          </div>

          <!-- Dettagli Prenotazione -->
          <div class="form-section">
            <h3>🏢 Dettagli Prenotazione</h3>
            
            <div class="form-group">
              <label for="booking_area">Area/Laboratorio *</label>
              <select 
                id="booking_area"
                formControlName="booking_area"
                [class.error]="isFieldInvalid('booking_area')"
              >
                <option value="">Seleziona un'area</option>
                <option *ngFor="let area of areas" [value]="area">{{ area }}</option>
              </select>
              <div class="error-message" *ngIf="isFieldInvalid('booking_area')">
                Area è obbligatoria
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label for="booking_date">Data *</label>
                <input 
                  type="date" 
                  id="booking_date"
                  formControlName="booking_date"
                  [class.error]="isFieldInvalid('booking_date')"
                >
                <div class="error-message" *ngIf="isFieldInvalid('booking_date')">
                  Data è obbligatoria
                </div>
              </div>

              <div class="form-group">
                <label for="booking_time">Orario *</label>
                <input 
                  type="time" 
                  id="booking_time"
                  formControlName="booking_time"
                  [class.error]="isFieldInvalid('booking_time')"
                >
                <div class="error-message" *ngIf="isFieldInvalid('booking_time')">
                  Orario è obbligatorio
                </div>
              </div>

              <div class="form-group">
                <label for="booking_duration">Durata *</label>
                <select 
                  id="booking_duration"
                  formControlName="booking_duration"
                  [class.error]="isFieldInvalid('booking_duration')"
                >
                  <option value="">Seleziona durata</option>
                  <option value="30 minuti">30 minuti</option>
                  <option value="1 ora">1 ora</option>
                  <option value="1 ora e 30 minuti">1 ora e 30 minuti</option>
                  <option value="2 ore">2 ore</option>
                  <option value="3 ore">3 ore</option>
                  <option value="4 ore">4 ore</option>
                  <option value="Mezza giornata">Mezza giornata</option>
                  <option value="Giornata intera">Giornata intera</option>
                </select>
                <div class="error-message" *ngIf="isFieldInvalid('booking_duration')">
                  Durata è obbligatoria
                </div>
              </div>
            </div>

            <div class="form-group">
              <label for="booking_purpose">Scopo della Prenotazione *</label>
              <textarea 
                id="booking_purpose"
                formControlName="booking_purpose"
                [class.error]="isFieldInvalid('booking_purpose')"
                rows="3"
              ></textarea>
              <div class="error-message" *ngIf="isFieldInvalid('booking_purpose')">
                Scopo è obbligatorio
              </div>
            </div>

            <div class="form-group">
              <label for="status">Status</label>
              <select id="status" formControlName="status">
                <option value="pending">In Attesa</option>
                <option value="confirmed">Confermata</option>
                <option value="cancelled">Annullata</option>
              </select>
            </div>
          </div>

          <!-- Azioni -->
          <div class="form-actions">
            <button type="button" class="btn-cancel" (click)="onCancel()" [disabled]="isSubmitting">
              Annulla
            </button>
            <button type="submit" class="btn-save" [disabled]="editForm.invalid || isSubmitting">
              <span *ngIf="isSubmitting" class="spinner"></span>
              {{ isSubmitting ? 'Salvando...' : 'Salva Modifiche' }}
            </button>
          </div>
        </form>

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
      max-width: 600px;
      max-height: 90vh;
      overflow-y: auto;
      box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
      font-family: 'Montserrat', sans-serif;
    }

    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1.5rem;
      border-bottom: 1px solid #e5e7eb;
      background: #f8f9fa;
      border-radius: 12px 12px 0 0;

      h2 {
        color: #2A4C92;
        font-weight: 600;
        margin: 0;
        font-size: 1.5rem;
      }

      .close-btn {
        background: none;
        border: none;
        font-size: 1.5rem;
        cursor: pointer;
        color: #666;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        transition: all 0.2s;

        &:hover {
          background: #e5e7eb;
          color: #374151;
        }
      }
    }

    .edit-form {
      padding: 1.5rem;
    }

    .form-section {
      margin-bottom: 2rem;

      h3 {
        color: #2A4C92;
        font-weight: 600;
        margin-bottom: 1rem;
        font-size: 1.1rem;
        border-bottom: 2px solid #e5e7eb;
        padding-bottom: 0.5rem;
      }
    }

    .form-group {
      margin-bottom: 1rem;

      label {
        display: block;
        font-weight: 500;
        color: #374151;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
      }

      input, select, textarea {
        width: 100%;
        padding: 0.75rem;
        border: 2px solid #e5e7eb;
        border-radius: 8px;
        font-size: 1rem;
        font-family: inherit;
        transition: border-color 0.2s;
        box-sizing: border-box;

        &:focus {
          outline: none;
          border-color: #2A4C92;
          box-shadow: 0 0 0 3px rgba(42, 76, 146, 0.1);
        }

        &.error {
          border-color: #dc2626;
          box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.1);
        }
      }

      textarea {
        resize: vertical;
        min-height: 80px;
      }
    }

    .form-row {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 1rem;

      @media (max-width: 768px) {
        grid-template-columns: 1fr;
      }
    }

    .error-message {
      color: #dc2626;
      font-size: 0.8rem;
      margin-top: 0.25rem;
      font-weight: 500;
    }

    .form-actions {
      display: flex;
      gap: 1rem;
      justify-content: flex-end;
      padding-top: 1rem;
      border-top: 1px solid #e5e7eb;
      margin-top: 2rem;
    }

    .btn-cancel, .btn-save {
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
      background: #f8f9fa;
      color: #374151;
      border: 1px solid #e5e7eb;

      &:hover:not(:disabled) {
        background: #e5e7eb;
      }
    }

    .btn-save {
      background: #2A4C92;
      color: white;

      &:hover:not(:disabled) {
        background: #1e3a7a;
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

    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  `]
})
export class BookingEditModalComponent implements OnInit, OnChanges {
  @Input() isVisible = false;
  @Input() booking: Booking | null = null;
  @Output() bookingUpdated = new EventEmitter<Booking>();
  @Output() cancelled = new EventEmitter<void>();

  editForm: FormGroup;
  isSubmitting = false;
  errorMessage = '';

  areas = [
    'Sala Angelo Marino',
    'Dipartimento NED',
    'Laboratorio',
    'Virtual Reality Center',
    'Sala Riunioni',
    'Laboratorio Materiali Compositi',
    'Centro R&D'
  ];

  constructor(
    private fb: FormBuilder,
    private bookingService: BookingService
  ) {
    this.editForm = this.createForm();
  }

  ngOnInit() {
    if (this.booking) {
      this.populateForm();
    }
  }

  ngOnChanges() {
    if (this.booking && this.editForm) {
      this.populateForm();
    }
  }

  private createForm(): FormGroup {
    return this.fb.group({
      visitor_name: ['', [Validators.required]],
      visitor_email: ['', [Validators.required, Validators.email]],
      visitor_phone: ['', [Validators.required]],
      booking_area: ['', [Validators.required]],
      booking_date: ['', [Validators.required]],
      booking_time: ['', [Validators.required]],
      booking_duration: ['', [Validators.required]],
      booking_purpose: ['', [Validators.required]],
      status: ['pending']
    });
  }

  private populateForm() {
    if (this.booking) {
      // Converte la data dal formato dd/mm/yyyy a yyyy-mm-dd per il form
      let formattedDate = this.booking.booking_date;
      if (/^\d{2}\/\d{2}\/\d{4}$/.test(this.booking.booking_date)) {
        const [day, month, year] = this.booking.booking_date.split('/');
        formattedDate = `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
      }

      this.editForm.patchValue({
        visitor_name: this.booking.visitor_name,
        visitor_email: this.booking.visitor_email,
        visitor_phone: this.booking.visitor_phone,
        booking_area: this.booking.booking_area,
        booking_date: formattedDate,
        booking_time: this.booking.booking_time,
        booking_duration: this.booking.booking_duration,
        booking_purpose: this.booking.booking_purpose,
        status: this.booking.status
      });
    }
  }

  isFieldInvalid(fieldName: string): boolean {
    const field = this.editForm.get(fieldName);
    return !!(field && field.invalid && (field.dirty || field.touched));
  }

  onSubmit() {
    if (this.editForm.valid && this.booking) {
      this.isSubmitting = true;
      this.errorMessage = '';

      const formValue = this.editForm.value;

      // Converte la data da yyyy-mm-dd a dd/mm/yyyy
      const [year, month, day] = formValue.booking_date.split('-');
      const formattedDate = `${day}/${month}/${year}`;

      const updatedBooking = {
        ...formValue,
        booking_date: formattedDate
      };

      this.bookingService.updateBooking(this.booking.id, updatedBooking).subscribe({
        next: (response) => {
          if (response.success) {
            this.bookingUpdated.emit(response.data);
            this.onCancel();
          } else {
            this.errorMessage = response.message || 'Errore durante l\'aggiornamento';
          }
          this.isSubmitting = false;
        },
        error: (error) => {
          console.error('Errore update:', error);
          this.errorMessage = 'Errore durante l\'aggiornamento della prenotazione';
          this.isSubmitting = false;
        }
      });
    }
  }

  onCancel() {
    this.editForm.reset();
    this.errorMessage = '';
    this.isSubmitting = false;
    this.cancelled.emit();
  }
}