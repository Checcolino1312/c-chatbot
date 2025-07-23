import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { ReactiveFormsModule } from '@angular/forms';
import { BookingEditModalComponent } from './booking-edit-modal.component';
import { BookingDeleteModalComponent } from './booking-delete-modal.component';
import { BookingService, Booking } from '../services/booking.service';


@Component({
  selector: 'app-booking',
  standalone: true,
  imports: [
    CommonModule, 
    FormsModule, 
    ReactiveFormsModule,
    BookingEditModalComponent,
    BookingDeleteModalComponent
  ],
  templateUrl: './booking.component.html',
  styleUrls: ['./booking.component.scss']
})
export class BookingComponent implements OnInit {
  bookings: Booking[] = [];
  filteredBookings: Booking[] = [];
  isLoading = false;
  errorMessage = '';
  
  // Filtri
  selectedArea = '';
  selectedStatus = '';
  selectedDate = '';

  // Modal states
  showEditModal = false;
  showDeleteModal = false;
  selectedBooking: Booking | null = null;

  // Opzioni per i filtri
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
    private http: HttpClient,
    private bookingService: BookingService
  ) {}

  ngOnInit() {
    this.loadBookings();
  }

  async loadBookings() {
    this.isLoading = true;
    this.errorMessage = '';
    
    try {
      console.log('🔄 Chiamando API...');
      const response = await this.bookingService.getAllBookings().toPromise();
      console.log('✅ Risposta API completa:', response);
      
      if (response && response.success && response.data) {
        this.bookings = response.data;
        console.log('📊 Prenotazioni caricate:', this.bookings);
      } else {
        console.log('⚠️ Nessuna prenotazione trovata');
        this.bookings = [];
      }
      
      this.filteredBookings = [...this.bookings];
      
    } catch (error) {
      console.error('❌ Errore API:', error);
      this.errorMessage = 'Errore nel caricamento delle prenotazioni dal database';
      
      // Dati di esempio per fallback
      this.bookings = [
        {
          id: 1,
          visitor_name: 'Mario Rossi',
          visitor_email: 'mario.rossi@email.com',
          visitor_phone: '+39 123 456 7890',
          booking_area: 'Laboratorio Materiali Compositi',
          booking_date: '25/07/2025',
          booking_time: '10:00',
          booking_duration: '2 ore',
          booking_purpose: 'Test di resistenza materiali per progetto automotive nel settore dei trasporti',
          created_at: '2025-07-23T10:00:00Z',
          status: 'confirmed'
        },
        {
          id: 2,
          visitor_name: 'Giulia Verdi',
          visitor_email: 'giulia.verdi@email.com',
          visitor_phone: '+39 987 654 3210',
          booking_area: 'Virtual Reality Center',
          booking_date: '26/07/2025',
          booking_time: '14:30',
          booking_duration: '3 ore',
          booking_purpose: 'Sviluppo applicazione VR per training industriale',
          created_at: '2025-07-23T11:30:00Z',
          status: 'pending'
        }
      ];
      this.filteredBookings = [...this.bookings];
    } finally {
      this.isLoading = false;
    }
  }

  // Metodi per filtri (già esistenti)
  applyFilters() {
    this.filteredBookings = this.bookings.filter(booking => {
      const areaMatch = !this.selectedArea || booking.booking_area === this.selectedArea;
      const statusMatch = !this.selectedStatus || booking.status === this.selectedStatus;
      const dateMatch = !this.selectedDate || booking.booking_date === this.selectedDate;
      
      return areaMatch && statusMatch && dateMatch;
    });
  }

  clearFilters() {
    this.selectedArea = '';
    this.selectedStatus = '';
    this.selectedDate = '';
    this.filteredBookings = [...this.bookings];
  }

  refreshData() {
    this.loadBookings();
  }

  // Nuovi metodi per CRUD
  onEditBooking(booking: Booking) {
    this.selectedBooking = booking;
    this.showEditModal = true;
  }

  onDeleteBooking(booking: Booking) {
    this.selectedBooking = booking;
    this.showDeleteModal = true;
  }

  onBookingUpdated(updatedBooking: Booking) {
    const index = this.bookings.findIndex(b => b.id === updatedBooking.id);
    if (index !== -1) {
      this.bookings[index] = updatedBooking;
      this.applyFilters(); // Riapplica i filtri
    }
    this.showEditModal = false;
    this.selectedBooking = null;
  }

  onBookingDeleted(bookingId: number) {
    this.bookings = this.bookings.filter(b => b.id !== bookingId);
    this.applyFilters(); // Riapplica i filtri
    this.showDeleteModal = false;
    this.selectedBooking = null;
  }

  onEditCancelled() {
    this.showEditModal = false;
    this.selectedBooking = null;
  }

  onDeleteCancelled() {
    this.showDeleteModal = false;
    this.selectedBooking = null;
  }

  // Metodo per aggiornamento rapido dello status
  onQuickStatusChange(booking: Booking, newStatus: Booking['status']) {
    this.bookingService.updateBookingStatus(booking.id, newStatus).subscribe({
      next: (response) => {
        if (response.success) {
          const index = this.bookings.findIndex(b => b.id === booking.id);
          if (index !== -1) {
            this.bookings[index] = response.data;
            this.applyFilters();
          }
        }
      },
      error: (error) => {
        console.error('Errore aggiornamento status:', error);
        // Potresti mostrare un toast di errore qui
      }
    });
  }

  // Metodi helper (già esistenti)
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

  formatDate(dateString: string): string {
    let date: Date;

    if (/^\d{2}\/\d{2}\/\d{4}$/.test(dateString)) {
      const [day, month, year] = dateString.split('/');
      date = new Date(Number(year), Number(month) - 1, Number(day));
    } else {
      date = new Date(dateString);
    }

    if (isNaN(date.getTime())) {
      throw new Error(`Formato data non valido: ${dateString}`);
    }

    return date.toLocaleDateString('it-IT', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }

  formatDateTime(dateString: string): string {
    return new Date(dateString).toLocaleString('it-IT', {
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  formatDuration(duration: string): string {
    return duration;
  }

  calculateEndTime(startTime: string, duration: number): string {
    const [hours, minutes] = startTime.split(':').map(Number);
    const startDate = new Date();
    startDate.setHours(hours, minutes, 0, 0);
    
    const endDate = new Date(startDate.getTime() + duration * 60000);
    
    return endDate.toTimeString().slice(0, 5);
  }

  getBookingsByStatus() {
    return {
      pending: this.bookings.filter(b => b.status === 'pending').length,
      confirmed: this.bookings.filter(b => b.status === 'confirmed').length,
      cancelled: this.bookings.filter(b => b.status === 'cancelled').length
    };
  }

getTodayBookings(): Booking[] {
  const today = new Date();
  const day = String(today.getDate()).padStart(2, '0');
  const month = String(today.getMonth() + 1).padStart(2, '0');
  const year = today.getFullYear();
  
  const todayStr = `${day}/${month}/${year}`; // formato gg/mm/aaaa

  return this.bookings.filter(b => b.booking_date === todayStr);
}


getUpcomingBookings(): Booking[] {
  const today = new Date();
  today.setHours(0, 0, 0, 0); // Normalizzo a mezzanotte

  return this.bookings
    .filter(b => {
      const [day, month, year] = b.booking_date.split('/').map(Number);
      const bookingDate = new Date(year, month - 1, day);

      return bookingDate > today && b.status !== 'cancelled';
    })
    .sort((a, b) => {
      const [dayA, monthA, yearA] = a.booking_date.split('/').map(Number);
      const [dayB, monthB, yearB] = b.booking_date.split('/').map(Number);

      const dateA = new Date(yearA, monthA - 1, dayA, ...a.booking_time.split(':').map(Number));
      const dateB = new Date(yearB, monthB - 1, dayB, ...b.booking_time.split(':').map(Number));

      return dateA.getTime() - dateB.getTime();
    })
    .slice(0, 5);
}

}