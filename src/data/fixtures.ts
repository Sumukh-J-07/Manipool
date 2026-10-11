import { Location, Student, VehicleOption } from '../types/domain';
export const demoProfile: Student = {
  id: 'you',
  name: 'Prathyush',
  email: 'prathyush@learner.manipal.edu',
  area: 'MAHE Campus',
};
export const students: Student[] = [
  {
    id: 'ananya',
    name: 'Ananya',
    email: 'ananya@learner.manipal.edu',
    area: 'Campus area',
  },
  {
    id: 'rahul',
    name: 'Rahul',
    email: 'rahul@learner.manipal.edu',
    area: 'Yelahanka area',
  },
  {
    id: 'sneha',
    name: 'Sneha',
    email: 'sneha@learner.manipal.edu',
    area: 'Bagalur area',
  },
];
export const locations: Location[] = [
  {
    id: 'campus',
    name: 'MAHE Bengaluru Campus',
    area: 'Govindapura, Yelahanka',
    kind: 'campus',
    corridor: 'campus',
  },
  {
    id: 'gate',
    name: 'Campus main gate',
    area: 'MAHE Bengaluru',
    kind: 'campus',
    corridor: 'campus',
  },
  {
    id: 'yelahanka',
    name: 'Yelahanka New Town',
    area: 'North Bengaluru',
    kind: 'city',
    corridor: 'north',
  },
  {
    id: 'airport',
    name: 'Kempegowda Airport',
    area: 'Terminal 1 • Bengaluru',
    kind: 'airport',
    corridor: 'airport',
  },
  {
    id: 'metro',
    name: 'Yeshwanthpur Metro',
    area: 'Green Line • Bengaluru',
    kind: 'metro',
    corridor: 'west',
  },
  {
    id: 'railway',
    name: 'Yeshwanthpur Railway Station',
    area: 'Bengaluru',
    kind: 'railway',
    corridor: 'west',
  },
  {
    id: 'majestic',
    name: 'Majestic Bus Station',
    area: 'Kempegowda Bus Station',
    kind: 'bus',
    corridor: 'central',
  },
  {
    id: 'church',
    name: 'Church Street',
    area: 'Central Bengaluru',
    kind: 'city',
    corridor: 'central',
  },
];
export const vehicleOptions: VehicleOption[] = [
  { id: 'cab', name: 'Shared cab', capacity: 4, farePaise: 84000 },
  { id: 'auto', name: 'Shared auto', capacity: 2, farePaise: 62000 },
];
export const quickMessages = [
  '5 minutes away',
  "I've arrived",
  'Running late',
  'Confirm pickup',
  'Can we leave 10 minutes later?',
  'Ride booked',
  "I'm cancelling",
];
export const matchingConfig = {
  pickupKm: 2,
  detourMinutes: 8,
  capacity: 4,
  weights: {
    route: 0.35,
    detour: 0.25,
    time: 0.2,
    destination: 0.15,
    reliability: 0.05,
  },
};
export function getLocation(id: string) {
  return locations.find(location => location.id === id);
}
