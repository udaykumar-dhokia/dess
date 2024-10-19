// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract EmailStorage {
    struct Email {
        string sender;
        string recipient;
        string subject;
        string body; // This should be encrypted
        uint256 timestamp;
    }

    mapping(uint256 => Email) private emails; // Store emails
    mapping(address => uint256[]) private userEmails; // Map user addresses to their email IDs
    uint256 private emailCounter;

    event EmailSent(
        uint256 emailId,
        string sender,
        string recipient,
        string subject,
        uint256 timestamp
    );

    constructor() {
        emailCounter = 0;
    }

    // Function to send an email
    function sendEmail(
        string memory sender,
        string memory recipient,
        string memory subject,
        string memory body
    ) public returns (uint256) {
        Email memory newEmail = Email({
            sender: sender,
            recipient: recipient,
            subject: subject,
            body: body,
            timestamp: block.timestamp
        });

        emails[emailCounter] = newEmail;
        userEmails[msg.sender].push(emailCounter);

        emit EmailSent(emailCounter, sender, recipient, subject, block.timestamp);
        emailCounter++;

        return emailCounter - 1; // Return the email ID
    }

    // Function to get an email by ID
    function getEmail(uint256 emailId) public view returns (Email memory) {
        require(emailId < emailCounter, "Email does not exist.");
        return emails[emailId];
    }

    // Function to get all email IDs sent by the sender
    function getEmailsBySender() public view returns (uint256[] memory) {
        return userEmails[msg.sender];
    }
}
