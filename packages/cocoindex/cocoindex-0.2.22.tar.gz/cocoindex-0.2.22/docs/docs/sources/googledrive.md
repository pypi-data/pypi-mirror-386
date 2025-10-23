---
title: GoogleDrive
toc_max_heading_level: 4
description: CocoIndex GoogleDrive Built-in Sources
---

The `GoogleDrive` source imports files from Google Drive.

### Setup for Google Drive

To access files in Google Drive, the `GoogleDrive` source will need to authenticate by service accounts.

1.  Register / login in **Google Cloud**.
2.  In [**Google Cloud Console**](https://console.cloud.google.com/), search for *Service Accounts*, to enter the *IAM & Admin / Service Accounts* page.
    -   **Create a new service account**: Click *+ Create Service Account*. Follow the instructions to finish service account creation.
    -   **Add a key and download the credential**: Under "Actions" for this new service account, click *Manage keys* → *Add key* → *Create new key* → *JSON*.
      Download the key file to a safe place.
3.  In **Google Cloud Console**, search for *Google Drive API*. Enable this API.
4.  In **Google Drive**, share the folders containing files that need to be imported through your source with the service account's email address.
    **Viewer permission** is sufficient.
    -   The email address can be found under the *IAM & Admin / Service Accounts* page (in Step 2), in the format of `{service-account-id}@{gcp-project-id}.iam.gserviceaccount.com`.
    -   Copy the folder ID. Folder ID can be found from the last part of the folder's URL, e.g. `https://drive.google.com/drive/u/0/folders/{folder-id}` or `https://drive.google.com/drive/folders/{folder-id}?usp=drive_link`.


### Spec

The spec takes the following fields:

*   `service_account_credential_path` (`str`): full path to the service account credential file in JSON format.
*   `root_folder_ids` (`list[str]`): a list of Google Drive folder IDs to import files from.
*   `binary` (`bool`, optional): whether reading files as binary (instead of text).
*   `recent_changes_poll_interval` (`datetime.timedelta`, optional): when set, this source provides a change capture mechanism by polling Google Drive for recent modified files periodically.

    :::info

    Since it only retrieves metadata for recent modified files (up to the previous poll) during polling,
    it's typically cheaper than a full refresh by setting the [refresh interval](/docs/core/flow_def#refresh-interval) especially when the folder contains a large number of files.
    So you can usually set it with a smaller value compared to the `refresh_interval`.

    On the other hand, this only detects changes for files that still exist.
    If the file is deleted (or the current account no longer has access to it), this change will not be detected by this change stream.

    So when a `GoogleDrive` source has `recent_changes_poll_interval` enabled, it's still recommended to set a `refresh_interval`, with a larger value.
    So that most changes can be covered by polling recent changes (with low latency, like 10 seconds), and remaining changes (files no longer exist or accessible) will still be covered (with a higher latency, like 5 minutes, and should be larger if you have a huge number of files like 1M).
    In reality, configure them based on your requirement: how fresh do you need the target index to be?

    :::

### Schema

The output is a [*KTable*](/docs/core/data_types#ktable) with the following sub fields:

*   `file_id` (*Str*, key): the ID of the file in Google Drive.
*   `filename` (*Str*): the filename of the file, without the path, e.g. `"file1.md"`
*   `mime_type` (*Str*): the MIME type of the file.
*   `content` (*Str* if `binary` is `False`, otherwise *Bytes*): the content of the file.
