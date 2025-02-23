package com.linkedin.datahub.graphql.resolvers.glossary;

import com.datahub.authentication.Authentication;
import com.linkedin.common.urn.GlossaryNodeUrn;
import com.linkedin.datahub.graphql.QueryContext;
import com.linkedin.datahub.graphql.generated.CreateGlossaryEntityInput;
import com.linkedin.datahub.graphql.resolvers.mutate.MutationUtils;
import com.linkedin.entity.client.EntityClient;
import com.linkedin.glossary.GlossaryTermInfo;
import com.linkedin.metadata.key.GlossaryTermKey;
import com.linkedin.metadata.entity.EntityService;
import com.linkedin.mxe.MetadataChangeProposal;
import graphql.schema.DataFetchingEnvironment;
import org.mockito.Mockito;
import org.testng.annotations.Test;

import static com.linkedin.datahub.graphql.TestUtils.getMockAllowContext;
import static com.linkedin.metadata.Constants.*;


public class CreateGlossaryTermResolverTest {

  private static final CreateGlossaryEntityInput TEST_INPUT = new CreateGlossaryEntityInput(
      "test-id",
      "test-name",
      "test-description",
      "urn:li:glossaryNode:12372c2ec7754c308993202dc44f548b"
  );
  private static final CreateGlossaryEntityInput TEST_INPUT_NO_DESCRIPTION = new CreateGlossaryEntityInput(
      "test-id",
      "test-name",
      null,
      "urn:li:glossaryNode:12372c2ec7754c308993202dc44f548b"
  );

  private static final CreateGlossaryEntityInput TEST_INPUT_NO_PARENT_NODE = new CreateGlossaryEntityInput(
      "test-id",
      "test-name",
      "test-description",
      null
  );

  private final String parentNodeUrn = "urn:li:glossaryNode:12372c2ec7754c308993202dc44f548b";

  private MetadataChangeProposal setupTest(
      DataFetchingEnvironment mockEnv,
      CreateGlossaryEntityInput input,
      String description,
      String parentNode
  ) throws Exception {
    QueryContext mockContext = getMockAllowContext();
    Mockito.when(mockContext.getAuthentication()).thenReturn(Mockito.mock(Authentication.class));
    Mockito.when(mockEnv.getArgument(Mockito.eq("input"))).thenReturn(input);
    Mockito.when(mockEnv.getContext()).thenReturn(mockContext);

    final GlossaryTermKey key = new GlossaryTermKey();
    key.setName("test-id");
    GlossaryTermInfo props = new GlossaryTermInfo();
    props.setDefinition(description);
    props.setName("test-name");
    props.setTermSource("INTERNAL");
    if (parentNode != null) {
      final GlossaryNodeUrn parent = GlossaryNodeUrn.createFromString(parentNode);
      props.setParentNode(parent);
    }
    return MutationUtils.buildMetadataChangeProposalWithKey(key, GLOSSARY_TERM_ENTITY_NAME,
        GLOSSARY_TERM_INFO_ASPECT_NAME, props);
  }

  @Test
  public void testGetSuccess() throws Exception {
    EntityClient mockClient = Mockito.mock(EntityClient.class);
    EntityService mockService = Mockito.mock(EntityService.class);
    DataFetchingEnvironment mockEnv = Mockito.mock(DataFetchingEnvironment.class);
    final MetadataChangeProposal proposal = setupTest(mockEnv, TEST_INPUT, "test-description", parentNodeUrn);

    CreateGlossaryTermResolver resolver = new CreateGlossaryTermResolver(mockClient, mockService);
    resolver.get(mockEnv).get();

    Mockito.verify(mockClient, Mockito.times(1)).ingestProposal(
        Mockito.eq(proposal),
        Mockito.any(Authentication.class),
        Mockito.eq(false)
    );
  }

  @Test
  public void testGetSuccessNoDescription() throws Exception {
    EntityClient mockClient = Mockito.mock(EntityClient.class);
    EntityService mockService = Mockito.mock(EntityService.class);
    DataFetchingEnvironment mockEnv = Mockito.mock(DataFetchingEnvironment.class);
    final MetadataChangeProposal proposal = setupTest(mockEnv, TEST_INPUT_NO_DESCRIPTION, "", parentNodeUrn);

    CreateGlossaryTermResolver resolver = new CreateGlossaryTermResolver(mockClient, mockService);
    resolver.get(mockEnv).get();

    Mockito.verify(mockClient, Mockito.times(1)).ingestProposal(
        Mockito.eq(proposal),
        Mockito.any(Authentication.class),
        Mockito.eq(false)
    );
  }

  @Test
  public void testGetSuccessNoParentNode() throws Exception {
    EntityClient mockClient = Mockito.mock(EntityClient.class);
    EntityService mockService = Mockito.mock(EntityService.class);
    DataFetchingEnvironment mockEnv = Mockito.mock(DataFetchingEnvironment.class);
    final MetadataChangeProposal proposal = setupTest(mockEnv, TEST_INPUT_NO_PARENT_NODE, "test-description", null);

    CreateGlossaryTermResolver resolver = new CreateGlossaryTermResolver(mockClient, mockService);
    resolver.get(mockEnv).get();

    Mockito.verify(mockClient, Mockito.times(1)).ingestProposal(
        Mockito.eq(proposal),
        Mockito.any(Authentication.class),
        Mockito.eq(false)
    );
  }
}
