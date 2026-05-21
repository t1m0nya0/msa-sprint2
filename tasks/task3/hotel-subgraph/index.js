import { ApolloServer } from '@apollo/server';
import { startStandaloneServer } from '@apollo/server/standalone';
import { buildSubgraphSchema } from '@apollo/subgraph';
import gql from 'graphql-tag';

const MONOLITH_URL = process.env.MONOLITH_URL || 'http://hotelio-monolith:8080';

async function fetchHotel(id) {
  const resp = await fetch(`${MONOLITH_URL}/api/hotels/${id}`);
  if (!resp.ok) return null;
  const hotel = await resp.json();
  const name = (hotel.description || hotel.id || 'Hotel').split(' ').slice(0, 3).join(' ');
  return {
    id: hotel.id,
    name,
    city: hotel.city,
    stars: Math.round(hotel.rating || 0),
  };
}

const typeDefs = gql`
  type Hotel @key(fields: "id") {
    id: ID!
    name: String
    city: String
    stars: Int
  }

  type Query {
    hotelsByIds(ids: [ID!]!): [Hotel]
  }
`;

const resolvers = {
  Hotel: {
    __resolveReference: async ({ id }) => fetchHotel(id),
  },
  Query: {
    hotelsByIds: async (_, { ids }) => {
      const hotels = await Promise.all(ids.map((id) => fetchHotel(id)));
      return hotels.filter(Boolean);
    },
  },
};

const server = new ApolloServer({
  schema: buildSubgraphSchema([{ typeDefs, resolvers }]),
});

startStandaloneServer(server, {
  listen: { port: 4002 },
}).then(() => {
  console.log('Hotel subgraph ready at http://localhost:4002/');
});
