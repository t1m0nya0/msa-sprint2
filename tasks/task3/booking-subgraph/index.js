import { ApolloServer } from '@apollo/server';
import { startStandaloneServer } from '@apollo/server/standalone';
import { buildSubgraphSchema } from '@apollo/subgraph';
import gql from 'graphql-tag';
import { GraphQLError } from 'graphql';
import grpc from '@grpc/grpc-js';
import protoLoader from '@grpc/proto-loader';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const packageDefinition = protoLoader.loadSync(path.join(__dirname, 'booking.proto'), {
  keepCase: true,
  longs: String,
  enums: String,
  defaults: true,
  oneofs: true,
});
const bookingProto = grpc.loadPackageDefinition(packageDefinition).booking;

const bookingClient = new bookingProto.BookingService(
  process.env.BOOKING_GRPC_HOST || 'booking-service:9090',
  grpc.credentials.createInsecure()
);

function listBookings(userId) {
  return new Promise((resolve, reject) => {
    bookingClient.ListBookings({ user_id: userId }, (err, response) => {
      if (err) return reject(err);
      resolve(response.bookings || []);
    });
  });
}

function assertBookingAccess(headerUserId, requestedUserId) {
  if (!headerUserId) {
    throw new GraphQLError('Требуется заголовок userid для доступа к бронированиям', {
      extensions: { code: 'UNAUTHENTICATED' },
    });
  }
  if (headerUserId !== requestedUserId) {
    throw new GraphQLError(
      `Доступ запрещён: можно просматривать только свои бронирования (userid=${headerUserId}, запрошен userId=${requestedUserId})`,
      { extensions: { code: 'FORBIDDEN' } },
    );
  }
}

const typeDefs = gql`
  type Booking @key(fields: "id") {
    id: ID!
    userId: String!
    hotelId: String!
    promoCode: String
    discountPercent: Int
    hotel: Hotel
  }

  type Hotel @key(fields: "id") {
    id: ID!
  }

  type Query {
    bookingsByUser(userId: String!): [Booking]
  }
`;

const resolvers = {
  Query: {
    bookingsByUser: async (_, { userId }, { req }) => {
      const headerUserId = req.headers['userid'];
      assertBookingAccess(headerUserId, userId);
      const bookings = await listBookings(userId);
      return bookings.map((b) => ({
        id: b.id,
        userId: b.user_id,
        hotelId: b.hotel_id,
        promoCode: b.promo_code || null,
        discountPercent: Math.round(b.discount_percent || 0),
      }));
    },
  },
  Booking: {
    hotel: (booking) => ({ __typename: 'Hotel', id: booking.hotelId }),
    __resolveReference: async (ref, { req }) => {
      const headerUserId = req.headers['userid'];
      if (!headerUserId) {
        throw new GraphQLError('Требуется заголовок userid', {
          extensions: { code: 'UNAUTHENTICATED' },
        });
      }
      const bookings = await listBookings(headerUserId);
      const booking = bookings.find((b) => b.id === ref.id);
      if (!booking || booking.user_id !== headerUserId) {
        throw new GraphQLError(`Бронирование ${ref.id} недоступно для пользователя ${headerUserId}`, {
          extensions: { code: 'FORBIDDEN' },
        });
      }
      return {
        id: booking.id,
        userId: booking.user_id,
        hotelId: booking.hotel_id,
        promoCode: booking.promo_code || null,
        discountPercent: Math.round(booking.discount_percent || 0),
      };
    },
  },
};

const server = new ApolloServer({
  schema: buildSubgraphSchema([{ typeDefs, resolvers }]),
});

startStandaloneServer(server, {
  listen: { port: 4001 },
  context: async ({ req }) => ({ req }),
}).then(() => {
  console.log('Booking subgraph ready at http://localhost:4001/');
});
