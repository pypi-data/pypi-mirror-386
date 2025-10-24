import {
  Dialog,
  Icon,
  InputWrapper,
  List,
  Radio,
  Tooltip,
} from "@equinor/eds-core-react";
import { createFormHook } from "@tanstack/react-form";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "react-toastify";

import { FmuProject } from "#client";
import {
  projectGetProjectQueryKey,
  projectPatchAccessMutation,
} from "#client/@tanstack/react-query.gen";
import { Access } from "#client/types.gen";
import { Classification } from "#client/types.gen";
import {
  CancelButton,
  GeneralButton,
  SubmitButton,
} from "#components/form/button";
import { TextField } from "#components/form/field";
import {
  EditDialog,
  InfoBox,
  PageCode,
  PageHeader,
  PageList,
  PageSectionSpacer,
  PageText,
} from "#styles/common";
import { fieldContext, formContext } from "#utils/form";
import { requiredStringValidator } from "#utils/validator";

const { useAppForm: useAppFormAccessEditor } = createFormHook({
  fieldComponents: {
    TextField,
    Radio,
  },
  formComponents: {
    SubmitButton,
    CancelButton,
  },
  fieldContext,
  formContext,
});

function AccessEditorForm({
  accessData,
  isDialogOpen,
  setIsDialogOpen,
}: {
  accessData: Access | null | undefined;
  isDialogOpen: boolean;
  setIsDialogOpen: (open: boolean) => void;
}) {
  const closeDialog = ({ formReset }: { formReset: () => void }) => {
    formReset();
    setIsDialogOpen(false);
  };
  const queryClient = useQueryClient();
  const { mutate, isPending } = useMutation({
    ...projectPatchAccessMutation(),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: projectGetProjectQueryKey(),
      });
    },
  });

  const form = useAppFormAccessEditor({
    defaultValues: {
      assetName: accessData?.asset.name ?? "",
      classification: accessData?.classification ?? "",
    },

    onSubmit: ({ value, formApi }) => {
      mutate(
        {
          body: {
            asset: { name: value.assetName.trim() },
            classification: value.classification as Classification,
          },
        },
        {
          onSuccess: () => {
            toast.info("Successfully set access information");
            closeDialog({ formReset: formApi.reset });
          },
        },
      );
    },
  });

  return (
    <EditDialog open={isDialogOpen}>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          e.stopPropagation();
          void form.handleSubmit();
        }}
      >
        <Dialog.Header>
          <Dialog.Title>Access</Dialog.Title>
        </Dialog.Header>

        <Dialog.Content>
          <form.AppField
            name="assetName"
            validators={{ onBlur: requiredStringValidator() }}
          >
            {(field) => <field.TextField label="Sumo target asset" />}
          </form.AppField>

          <PageSectionSpacer />

          <form.AppField
            name="classification"
            validators={{ onChange: requiredStringValidator() }}
          >
            {(field) => (
              <InputWrapper
                label="Default security classification"
                color="error"
                helperProps={{
                  text: !field.state.meta.isValid ? "Required" : "",
                  icon: <Icon name="error_filled" size={16} />,
                }}
              >
                {["internal", "restricted"].map((option) => (
                  <Tooltip
                    key={option}
                    title={
                      option === "internal"
                        ? "Requires READ access to the asset"
                        : "Requires WRITE access to the asset"
                    }
                  >
                    <span>
                      <Radio
                        label={option}
                        checked={field.state.value === option}
                        onChange={() => {
                          field.handleChange(option);
                        }}
                      />
                    </span>
                  </Tooltip>
                ))}
              </InputWrapper>
            )}
          </form.AppField>
        </Dialog.Content>

        <Dialog.Actions>
          <form.Subscribe
            selector={(state) => [state.isDefaultValue, state.canSubmit]}
          >
            {([isDefaultValue, canSubmit]) => (
              <form.SubmitButton
                label="Save"
                disabled={isDefaultValue || !canSubmit}
                isPending={isPending}
              />
            )}
          </form.Subscribe>
          <form.CancelButton
            onClick={(e) => {
              e.preventDefault();
              closeDialog({ formReset: form.reset });
            }}
          />
        </Dialog.Actions>
      </form>
    </EditDialog>
  );
}

export function AccessInfo({ accessData }: { accessData: Access }) {
  return (
    <InfoBox>
      <table>
        <tbody>
          <tr>
            <th>Sumo target asset</th>
            <td>{accessData.asset.name}</td>
          </tr>
          <tr>
            <th>Default classification</th>
            <td>{accessData.classification}</td>
          </tr>
        </tbody>
      </table>
    </InfoBox>
  );
}

export function EditableAccessInfo({
  projectData,
}: {
  projectData: FmuProject;
}) {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const accessData = projectData.config.access;

  return (
    <>
      <PageHeader $variant="h3">Access control</PageHeader>

      <PageText>
        This section is used to configure access permissions for data exported
        from the project.
      </PageText>

      <PageText>
        The <i>asset</i> specifies the target asset in Sumo where data will be
        uploaded. The <i>classification</i> sets the default information
        classification for the data.
      </PageText>

      <PageList>
        <List.Item>
          internal - requires <i>READ</i> access to the asset
        </List.Item>
        <List.Item>
          restricted - requires <i>WRITE</i> access to the asset
        </List.Item>
      </PageList>

      <PageText>
        Read more about access control in the{" "}
        <a
          href="https://doc-sumo-doc-prod.radix.equinor.com/documentation/access_control"
          target="_blank"
          rel="noopener noreferrer"
        >
          Sumo documentation
        </a>
      </PageText>

      {accessData ? (
        <AccessInfo accessData={accessData} />
      ) : (
        <PageCode>No access information found in the project</PageCode>
      )}

      <GeneralButton
        label={accessData ? "Edit" : "Add"}
        onClick={() => {
          setIsDialogOpen(true);
        }}
      />

      <AccessEditorForm
        accessData={accessData}
        isDialogOpen={isDialogOpen}
        setIsDialogOpen={setIsDialogOpen}
      />
    </>
  );
}
