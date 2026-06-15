import { ApolloClient, InMemoryCache, gql } from "@apollo/client";

export const client = new ApolloClient({
  uri: "http://localhost:8000/graphql",
  cache: new InMemoryCache(),
});

export const BOOTSTRAP_QUERY = gql`
  query Bootstrap {
    incidents(limit: 30) {
      id
      kind
      severity
      summary
      customerMessage
      status
      createdAt
      resolutionKind
      savedAmount
      order {
        id
        amount
        product { name }
        customer { name tier }
      }
    }
    kpis {
      incidentsResolved
      incidentsEscalated
      savedRevenue
      escalationRate
      avgResolutionSeconds
      openIncidents
    }
    activeBrand {
      id
      name
      tagline
      logoSvg
      voice
      colors { background surface accent accentSoft text muted danger success }
    }
    brands { id name }
    simulationRunning
  }
`;

export const INJECT_INCIDENT = gql`
  mutation Inject($kind: IncidentKind!) {
    injectIncident(kind: $kind) { id }
  }
`;

export const SET_BRAND = gql`
  mutation SetBrand($brandId: ID!) {
    setBrand(brandId: $brandId) { id name }
  }
`;

export const SET_SIMULATION = gql`
  mutation SetSim($running: Boolean!) {
    setSimulation(running: $running)
  }
`;
