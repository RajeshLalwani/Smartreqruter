// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Certificate {
    struct Credential {
        string candidateId;
        string score;
        uint256 timestamp;
        bool exists;
    }

    // Mapping from a unique hash (CertificateHash) to the Credential details
    mapping(string => Credential) public certificates;

    event CertificateMinted(string indexed certificateHash, string candidateId, string score, uint256 timestamp);

    // Only the contract creator (the ATS backend) can mint certificates
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can mint certificates");
        _;
    }

    // Mint a new certificate
    function mintCertificate(string memory _hash, string memory _candidateId, string memory _score) public onlyOwner {
        require(!certificates[_hash].exists, "Certificate hash already exists");

        certificates[_hash] = Credential({
            candidateId: _candidateId,
            score: _score,
            timestamp: block.timestamp,
            exists: true
        });

        emit CertificateMinted(_hash, _candidateId, _score, block.timestamp);
    }

    // Verify a certificate
    function verifyCertificate(string memory _hash) public view returns (string memory, string memory, uint256, bool) {
        Credential memory cred = certificates[_hash];
        return (cred.candidateId, cred.score, cred.timestamp, cred.exists);
    }
}
