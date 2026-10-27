export type RideStatus =
  | 'DRAFT'
  | 'SEARCHING'
  | 'MATCH_FOUND'
  | 'WAITING_FOR_ACCEPTANCE'
  | 'GROUP_FORMED'
  | 'RIDE_BOOKED'
  | 'IN_PROGRESS'
  | 'COMPLETED'
  | 'NO_MATCH'
  | 'REMATCHING'
  | 'CANCELLED'
  | 'EXPIRED';
export type Flexibility = 0 | 15 | 30 | 45;
export type DemoScenario = 'normal' | 'no-match' | 'two-riders';
export interface Student {
  id: string;
  name: string;
  email: string;
  area: string;
}
export interface Location {
  id: string;
  name: string;
  area: string;
  kind: 'campus' | 'metro' | 'airport' | 'railway' | 'city' | 'bus';
  corridor: string;
}
export interface RideDraft {
  pickupId: string;
  destinationId: string;
  date: string;
  time: string;
  flexibility: Flexibility;
}
export interface MatchCandidate {
  id: string;
  student: Student;
  departure: string;
  flexibility: Flexibility;
  destinationId: string;
  corridor: string;
  pickupKm: number;
  detourMinutes: number;
  routeOverlap: number;
  reliability: number;
  score: number;
}
export interface RideRequest {
  id: string;
  userId: string;
  pickup: Location;
  destination: Location;
  departure: string;
  flexibility: Flexibility;
  createdAt: string;
  status: RideStatus;
  matches: MatchCandidate[];
  groupId?: string;
}
export interface ChatMessage {
  id: string;
  senderId: string;
  sender: string;
  text: string;
  timestamp: string;
  system: boolean;
}
export interface VehicleOption {
  id: 'cab' | 'auto';
  name: string;
  capacity: number;
  farePaise: number;
}
export interface RideBooking {
  option: VehicleOption;
  confirmedAt: string;
}
export interface CarpoolGroup {
  id: string;
  rideId: string;
  members: Student[];
  pickupMode: 'common' | 'sequential';
  status: 'GROUP_FORMED' | 'RIDE_BOOKED' | 'IN_PROGRESS' | 'COMPLETED';
  messages: ChatMessage[];
  booking?: RideBooking;
}
export interface DemoReport {
  id: string;
  rideId?: string;
  text: string;
  timestamp: string;
}
export interface AppState {
  profile: Student;
  signedIn: boolean;
  draft: RideDraft;
  rides: RideRequest[];
  groups: CarpoolGroup[];
  scenario: DemoScenario;
  notifications: boolean;
  savedPlaces: string[];
  reports: DemoReport[];
  token?: string;
  error?: string;
}
